from collections import defaultdict

from django.db.models import Avg, Count, Q, Sum

from core.models import AcademicClass, Section, Subject
from student.models import StudentProfile
from analytics.models import (
    AnalyticsExam,
    AnalyticsStudent,
    ExamSubject,
    ExamResult,
    QuestionResult,
    QuestionAnalytics,
    SectionAnalytics,
    StudentRisk,
)
from analytics.constants import (
    ANALYTICS_STATUS_DONE,
    ANALYTICS_STATUS_FAILED,
    ANALYTICS_STATUS_RUNNING,
)
from analytics.services.analytics_engine import (
    compute_question_analytics,
    compute_student_risks,
    compute_section_analytics,
)


class AnalyticsDB:

    # ---------------------------------------------------------------- profile

    def get_principal_profile(self, user):
        if user.role == 'ADMIN':
            return getattr(user, 'adminprofile', None)
        return getattr(user, 'principalprofile', None)

    def get_teacher_profile(self, user):
        return getattr(user, 'teacherprofile', None)

    def get_student_profile(self, user):
        return self.get_analytics_student_by_user(user)

    # --------------------------------------------------------- upload pipeline

    def create_exam(self, school, exam_name, exam_date, uploaded_by):
        from analytics.constants import ANALYTICS_STATUS_PENDING
        return AnalyticsExam.objects.create(
            school=school,
            exam_name=exam_name,
            exam_date=exam_date,
            uploaded_by=uploaded_by,
            analytics_status=ANALYTICS_STATUS_PENDING,
        )

    def create_exam_record(self, school, exam_name, class_id=None, section_id=None):
        return AnalyticsExam.objects.create(
            school=school,
            exam_name=exam_name,
            academic_class_id=class_id,
            section_id=section_id,
        )

    def get_exam_for_upload(self, exam_id, school_id):
        try:
            return AnalyticsExam.objects.get(id=exam_id, school_id=school_id)
        except AnalyticsExam.DoesNotExist:
            return None

    def update_exam_on_upload(self, exam, exam_date, uploaded_by):
        from analytics.constants import ANALYTICS_STATUS_PENDING
        exam.exam_date = exam_date
        exam.uploaded_by = uploaded_by
        exam.analytics_status = ANALYTICS_STATUS_PENDING
        exam.save(update_fields=['exam_date', 'uploaded_by', 'analytics_status', 'updated_at'])
        return exam

    def get_or_create_core_subject(self, school, subject_name):
        subject = Subject.objects.filter(school=school, name__iexact=subject_name).first()
        if subject is None:
            subject = Subject.objects.create(school=school, name=subject_name)
        return subject

    def create_exam_subject(self, exam, subject_name, total_questions, max_marks, core_subject):
        return ExamSubject.objects.create(
            exam=exam,
            subject_name=subject_name,
            total_questions=total_questions,
            max_marks=max_marks,
            core_subject=core_subject,
        )

    def get_or_create_analytics_student(
        self, school, student_ref_id, name, class_name='', section_name=''
    ):
        section      = None
        academic_class = None
        linked_user  = None

        # Primary: match via StudentProfile.admission_number (most reliable)
        profile = StudentProfile.objects.filter(
            school=school, admission_number=student_ref_id
        ).select_related('section__academic_class', 'user').first()

        if profile:
            section        = profile.section
            academic_class = profile.academic_class
            linked_user    = profile.user
            class_name     = academic_class.name
            section_name   = section.name
        else:
            # Fallback: text-based matching from CSV class/section columns
            if class_name and section_name:
                section = (
                    Section.objects
                    .filter(
                        school=school,
                        name__iexact=section_name,
                        academic_class__name__iexact=class_name,
                    )
                    .select_related('academic_class')
                    .first()
                )
            if section:
                academic_class = section.academic_class
            elif class_name:
                academic_class = AcademicClass.objects.filter(
                    school=school, name__iexact=class_name
                ).first()

        student, _ = AnalyticsStudent.objects.update_or_create(
            student_ref_id=student_ref_id,
            school=school,
            defaults={
                'name':         name,
                'class_name':   class_name,
                'section_name': section_name,
                'section':      section,
                'academic_class': academic_class,
                'linked_user':  linked_user,
            },
        )
        return student

    def bulk_create_exam_results(self, records):
        ExamResult.objects.bulk_create(records, ignore_conflicts=True)

    def bulk_create_question_results(self, records):
        QuestionResult.objects.bulk_create(records, ignore_conflicts=True)

    # -------------------------------------------------- background analytics

    def run_analytics(self, exam_id):
        """
        Orchestrate the full pre-compute pipeline for one exam.

        Called in a daemon thread AFTER the upload transaction has committed,
        so all ExamResult / QuestionResult rows are visible.

        Order matters:
          1. QuestionAnalytics  (per subject)
          2. StudentRisk        (per subject)   — must exist before step 3
          3. SectionAnalytics   (per subject)   — reads StudentRisk for at_risk_count
        """
        try:
            exam = AnalyticsExam.objects.prefetch_related('subjects').get(id=exam_id)
        except AnalyticsExam.DoesNotExist:
            return

        exam.analytics_status = ANALYTICS_STATUS_RUNNING
        exam.save(update_fields=['analytics_status', 'updated_at'])

        try:
            # Pre-fetch all AnalyticsStudents who have results in this exam.
            # Reused in _write_student_risks to map UUID string → FK object.
            student_map = {
                str(s.id): s
                for s in AnalyticsStudent.objects.filter(results__exam=exam).distinct()
            }

            for exam_subject in exam.subjects.all():
                self._write_question_analytics(exam, exam_subject, student_map)
                self._write_student_risks(exam, exam_subject, student_map)

            # Section analytics reads StudentRisk, so runs after both loops above.
            for exam_subject in exam.subjects.all():
                self._write_section_analytics(exam, exam_subject)

            exam.analytics_status = ANALYTICS_STATUS_DONE
            exam.save(update_fields=['analytics_status', 'updated_at'])

        except Exception:
            exam.analytics_status = ANALYTICS_STATUS_FAILED
            exam.save(update_fields=['analytics_status', 'updated_at'])
            raise

    def _write_question_analytics(self, exam, exam_subject, student_map):
        q_results = list(
            QuestionResult.objects
            .filter(exam=exam, subject=exam_subject)
            .values('student_id', 'q_no', 'status')
        )
        subject_marks = list(
            ExamResult.objects
            .filter(exam=exam, subject=exam_subject)
            .values('student_id', 'total_marks')
        )

        results = compute_question_analytics(q_results, subject_marks)
        if not results:
            return

        QuestionAnalytics.objects.filter(exam=exam, subject=exam_subject).delete()
        QuestionAnalytics.objects.bulk_create([
            QuestionAnalytics(
                exam=exam,
                subject=exam_subject,
                q_no=r.q_no,
                correct_count=r.correct_count,
                wrong_count=r.wrong_count,
                skip_count=r.skip_count,
                difficulty_index=r.difficulty_index,
                difficulty_tag=r.difficulty_tag,
                discrimination_index=r.discrimination_index,
                has_key_error=r.has_key_error,
            )
            for r in results
        ])

    def _write_student_risks(self, exam, exam_subject, student_map):
        subject_results = list(
            ExamResult.objects
            .filter(exam=exam, subject=exam_subject)
            .values('student_id', 'total_marks', 'correct', 'wrong', 'unattempted')
        )

        results = compute_student_risks(subject_results, exam_subject.total_questions)
        if not results:
            return

        StudentRisk.objects.filter(exam=exam, subject=exam_subject).delete()
        StudentRisk.objects.bulk_create([
            StudentRisk(
                exam=exam,
                student=student_map[r.student_id],
                subject=exam_subject,
                risk_score=r.risk_score,
                risk_label=r.risk_label,
                z_score=r.z_score,
                performance_label=r.performance_label,
            )
            for r in results
            if r.student_id in student_map
        ])

    def _write_section_analytics(self, exam, exam_subject):
        rows = list(
            ExamResult.objects
            .filter(exam=exam, subject=exam_subject, student__section__isnull=False)
            .values('student__id', 'student__section_id', 'total_marks')
        )
        if not rows:
            return

        section_students = [
            {
                'student_id': str(r['student__id']),
                'section_id': str(r['student__section_id']),
                'total_marks': r['total_marks'],
            }
            for r in rows
        ]

        risk_by_student = {
            str(sr['student_id']): sr['risk_label']
            for sr in StudentRisk.objects
            .filter(exam=exam, subject=exam_subject)
            .values('student_id', 'risk_label')
        }

        results = compute_section_analytics(section_students, risk_by_student)
        if not results:
            return

        section_ids    = {r.section_id for r in results}
        top_scorer_ids = {r.top_scorer_id for r in results}

        section_map = {
            str(s.id): s
            for s in Section.objects.filter(id__in=section_ids).select_related('academic_class')
        }
        top_scorer_map = {
            str(s.id): s
            for s in AnalyticsStudent.objects.filter(id__in=top_scorer_ids)
        }

        SectionAnalytics.objects.filter(exam=exam, subject=exam_subject).delete()
        SectionAnalytics.objects.bulk_create(
            [
                SectionAnalytics(
                    exam=exam,
                    section=section_map[r.section_id],
                    academic_class=section_map[r.section_id].academic_class,
                    subject=exam_subject,
                    avg_marks=r.avg_marks,
                    median_marks=r.median_marks,
                    std_dev=r.std_dev,
                    top_scorer=top_scorer_map.get(r.top_scorer_id),
                    at_risk_count=r.at_risk_count,
                )
                for r in results
                if r.section_id in section_map
            ],
            ignore_conflicts=True,
        )

    # --------------------------------------------------------------- read API

    def get_exam_by_id(self, exam_id, school_id):
        try:
            return (
                AnalyticsExam.objects
                .select_related('academic_class', 'section')
                .prefetch_related('subjects')
                .get(id=exam_id, school_id=school_id)
            )
        except AnalyticsExam.DoesNotExist:
            return None

    def get_sections_for_class_ids(self, class_ids, school_id):
        return list(
            Section.objects
            .filter(academic_class_id__in=class_ids, school_id=school_id)
            .order_by('academic_class_id', 'name')
        )

    def get_exams_for_school(self, school_id):
        return list(
            AnalyticsExam.objects
            .filter(school_id=school_id)
            .select_related('academic_class', 'section')
            .prefetch_related('subjects')
        )

    def get_section_analytics_for_exam(self, exam_id):
        return list(
            SectionAnalytics.objects
            .filter(exam_id=exam_id)
            .select_related('section', 'academic_class', 'subject', 'top_scorer')
        )

    def get_subject_overall_stats(self, exam_id, school_id):
        """
        School-level stats per subject for Screen 1 subject_summary cards.
        Queries ExamResult directly so averages are exact (not biased
        average-of-section-averages).
        Returns a list of dicts ordered by subject_name.
        """
        subjects = list(
            ExamSubject.objects
            .filter(exam_id=exam_id, exam__school_id=school_id)
            .order_by('subject_name')
        )

        stats = []
        for es in subjects:
            agg = (
                ExamResult.objects
                .filter(exam_id=exam_id, subject=es)
                .aggregate(avg=Avg('total_marks'))
            )
            school_avg = round(agg['avg'] or 0.0, 2)

            top = (
                ExamResult.objects
                .filter(exam_id=exam_id, subject=es)
                .select_related('student')
                .order_by('-total_marks')
                .first()
            )

            stats.append({
                'subject_name':    es.subject_name,
                'total_questions': es.total_questions,
                'school_avg':      school_avg,
                'top_scorer': {
                    'name':            top.student.name,
                    'student_ref_id':  top.student.student_ref_id,
                    'marks':           top.total_marks,
                    'class_name':      top.student.class_name,
                    'section_name':    top.student.section_name,
                } if top else None,
            })
        return stats

    def get_class_by_id(self, class_id, school_id):
        try:
            return AcademicClass.objects.get(id=class_id, school_id=school_id)
        except AcademicClass.DoesNotExist:
            return None

    def get_section_analytics_for_class(self, exam_id, class_id, school_id):
        """
        Section-level analytics filtered by class UUID for Screen 2.
        Attaches _top_marks to each row (the top scorer's marks in
        that subject) via a single batch ExamResult query.
        """
        sa_list = list(
            SectionAnalytics.objects
            .filter(
                exam_id=exam_id,
                exam__school_id=school_id,
                academic_class_id=class_id,
            )
            .select_related('section', 'academic_class', 'subject', 'top_scorer')
            .order_by('section__name', 'subject__subject_name')
        )

        if not sa_list:
            return sa_list

        # Batch fetch top-scorer marks to avoid N+1 queries
        scorer_pairs = [
            (str(sa.top_scorer_id), str(sa.subject_id))
            for sa in sa_list if sa.top_scorer_id
        ]
        marks_lookup = {}
        if scorer_pairs:
            q = Q()
            for student_id, subject_id in scorer_pairs:
                q |= Q(student_id=student_id, subject_id=subject_id)
            for row in ExamResult.objects.filter(exam_id=exam_id).filter(q).values(
                'student_id', 'subject_id', 'total_marks'
            ):
                marks_lookup[(str(row['student_id']), str(row['subject_id']))] = row['total_marks']

        for sa in sa_list:
            if sa.top_scorer_id:
                sa._top_marks = marks_lookup.get((str(sa.top_scorer_id), str(sa.subject_id)))
            else:
                sa._top_marks = None

        return sa_list

    def get_student_counts_for_exam(self, exam_id, school_id):
        """
        Returns {section_id_str: student_count} for all sections in the exam.
        Used by Screen 2 to show how many students are in each section.
        """
        rows = (
            ExamResult.objects
            .filter(
                exam_id=exam_id,
                exam__school_id=school_id,
                student__section__isnull=False,
            )
            .values('student__section_id')
            .annotate(count=Count('student_id', distinct=True))
        )
        return {str(r['student__section_id']): r['count'] for r in rows}

    def get_exam_overview(self, exam_id, school_id):
        subjects = list(
            ExamSubject.objects
            .filter(exam_id=exam_id, exam__school_id=school_id)
            .order_by('subject_name')
        )
        class_avgs = []
        for es in subjects:
            agg = ExamResult.objects.filter(exam_id=exam_id, subject=es).aggregate(avg=Avg('total_marks'))
            class_avgs.append({
                'subject_id': str(es.id),
                'subject_name': es.subject_name,
                'avg': round(agg['avg'] or 0.0, 2),
                'max_marks': es.max_marks,
            })

        section_analytics = list(
            SectionAnalytics.objects
            .filter(exam_id=exam_id)
            .select_related('section', 'subject')
            .order_by('section__name')
        )
        by_section = defaultdict(list)
        section_names = {}
        for sa in section_analytics:
            sid = str(sa.section_id)
            by_section[sid].append(sa.avg_marks)
            section_names[sid] = sa.section.name

        sections = [
            {
                'section_id': sid,
                'section_name': section_names[sid],
                'avg': round(sum(avgs) / len(avgs), 2) if avgs else 0,
            }
            for sid, avgs in sorted(by_section.items(), key=lambda x: section_names[x[0]])
        ]
        return {'class_avgs': class_avgs, 'sections': sections}

    def get_top_students(self, exam_id, n=5):
        rows = (
            ExamResult.objects
            .filter(exam_id=exam_id)
            .values('student_id', 'student__name', 'student__student_ref_id')
            .annotate(total=Sum('total_marks'))
            .order_by('-total')[:n]
        )
        return [
            {
                'student_id': str(r['student_id']),
                'name': r['student__name'],
                'student_ref_id': r['student__student_ref_id'],
                'total_marks': r['total'],
                'rank': idx + 1,
            }
            for idx, r in enumerate(rows)
        ]

    def get_section_subject_detail(self, exam_id, section_id, school_id):
        section_sa = list(
            SectionAnalytics.objects
            .filter(exam_id=exam_id, section_id=section_id)
            .select_related('subject')
        )
        class_avgs = {}
        for sa in section_sa:
            agg = ExamResult.objects.filter(
                exam_id=exam_id, subject_id=sa.subject_id
            ).aggregate(avg=Avg('total_marks'))
            class_avgs[str(sa.subject_id)] = round(agg['avg'] or 0.0, 2)

        return [
            {
                'subject_id': str(sa.subject_id),
                'subject_name': sa.subject.subject_name,
                'section_avg': round(sa.avg_marks, 2),
                'class_avg': class_avgs.get(str(sa.subject_id), 0),
                'delta': round(sa.avg_marks - class_avgs.get(str(sa.subject_id), 0), 2),
            }
            for sa in sorted(section_sa, key=lambda x: x.subject.subject_name)
        ]

    def get_section_overview(self, exam_id, section_id):
        section_sa = list(
            SectionAnalytics.objects
            .filter(exam_id=exam_id, section_id=section_id)
            .select_related('subject')
        )
        return [
            {
                'subject_id':   str(sa.subject_id),
                'subject_name': sa.subject.subject_name,
                'avg':          round(sa.avg_marks, 2),
                'max_marks':    sa.subject.max_marks,
            }
            for sa in sorted(section_sa, key=lambda x: x.subject.subject_name)
        ]

    def get_class_question_students(self, exam_id, subject_id, q_no):
        rows = list(
            QuestionResult.objects
            .filter(exam_id=exam_id, subject_id=subject_id, q_no=q_no)
            .select_related('student')
            .order_by('student__name')
        )
        result = {'C': [], 'W': [], 'U': []}
        for qr in rows:
            result[qr.status].append({
                'student_id': str(qr.student_id),
                'student_ref_id': qr.student.student_ref_id,
                'name': qr.student.name,
            })
        return result

    def get_analytics_student_by_user(self, user):
        try:
            return AnalyticsStudent.objects.select_related(
                'school', 'section', 'academic_class'
            ).get(linked_user=user)
        except AnalyticsStudent.DoesNotExist:
            return None

    def get_exams_for_student(self, student_id, school_id):
        return list(
            AnalyticsExam.objects
            .filter(results__student_id=student_id, school_id=school_id)
            .select_related('academic_class', 'section')
            .prefetch_related('subjects')
            .distinct()
            .order_by('-exam_date', '-created_at')
        )

    def get_exams_for_teacher(self, teacher_profile, school_id):
        assigned_sections = list(teacher_profile.assigned_sections.all())
        class_ids = [s.academic_class_id for s in assigned_sections]
        return list(
            AnalyticsExam.objects
            .filter(
                Q(section__in=assigned_sections) | Q(academic_class_id__in=class_ids),
                school_id=school_id
            )
            .select_related('academic_class', 'section')
            .prefetch_related('subjects')
            .distinct()
            .order_by('-exam_date', '-created_at')
        )

    def get_subjects_for_student_exam(self, exam_id, student_id):
        return list(
            ExamResult.objects
            .filter(exam_id=exam_id, student_id=student_id)
            .select_related('subject')
            .order_by('subject__subject_name')
        )

    def get_question_results_for_section_question(
        self, exam_id, section_id, subject_id, q_no
    ):
        """
        Returns all QuestionResult rows for one specific question in a section,
        grouped into correct / wrong / unattempted lists.
        Each entry includes the student's name, id, and student_ref_id.
        """
        rows = list(
            QuestionResult.objects
            .filter(
                exam_id=exam_id,
                subject_id=subject_id,
                q_no=q_no,
                student__section_id=section_id,
            )
            .select_related('student')
            .order_by('student__name')
        )
        result = {'C': [], 'W': [], 'U': []}
        for qr in rows:
            result[qr.status].append({
                'student_id':     str(qr.student_id),
                'student_ref_id': qr.student.student_ref_id,
                'name':           qr.student.name,
            })
        return result

    def get_section_by_id(self, section_id, school_id):
        try:
            return Section.objects.select_related('academic_class').get(
                id=section_id, school_id=school_id,
            )
        except Section.DoesNotExist:
            return None

    def get_exam_subject_by_id(self, subject_id, exam_id):
        """Fetch an ExamSubject by UUID, scoped to the exam."""
        try:
            return ExamSubject.objects.get(id=subject_id, exam_id=exam_id)
        except ExamSubject.DoesNotExist:
            return None

    def get_question_analytics_for_subject(self, exam_id, subject_id):
        return list(
            QuestionAnalytics.objects
            .filter(exam_id=exam_id, subject_id=subject_id)
            .select_related('subject')
            .order_by('q_no')
        )

    def get_question_detail(self, exam_id, subject_id, q_no):
        try:
            return QuestionAnalytics.objects.select_related('subject').get(
                exam_id=exam_id,
                subject_id=subject_id,
                q_no=q_no,
            )
        except QuestionAnalytics.DoesNotExist:
            return None

    def get_exam_results_for_section(self, exam_id, class_name, section_name, school_id):
        """
        Returns ExamResult rows for all students in a given class+section,
        annotated with their risk data. Used by Screen 3 student table.
        """
        return list(
            ExamResult.objects
            .filter(
                exam_id=exam_id,
                exam__school_id=school_id,
                student__class_name__iexact=class_name,
                student__section_name__iexact=section_name,
            )
            .select_related('student', 'subject')
            .order_by('student__name', 'subject__subject_name')
        )

    def get_student_risks_for_section(self, exam_id, class_name, section_name, school_id):
        """
        Returns StudentRisk rows for all students in a section.
        Keyed by (student_id, subject_name) for fast lookup in the presenter.
        """
        risks = StudentRisk.objects.filter(
            exam_id=exam_id,
            exam__school_id=school_id,
            student__class_name__iexact=class_name,
            student__section_name__iexact=section_name,
        ).select_related('student', 'subject')
        return {
            (str(r.student_id), r.subject.subject_name): r
            for r in risks
        }

    def get_student_by_ref_id(self, student_ref_id, school_id):
        try:
            return AnalyticsStudent.objects.get(
                student_ref_id=student_ref_id, school_id=school_id
            )
        except AnalyticsStudent.DoesNotExist:
            return None

    def get_student_by_id(self, student_id, school_id):
        """Lookup AnalyticsStudent by UUID primary key, scoped to school."""
        try:
            return AnalyticsStudent.objects.select_related('section__academic_class').get(
                id=student_id, school_id=school_id
            )
        except AnalyticsStudent.DoesNotExist:
            return None

    # ------------------------------------------------------ Screen 6 queries

    def get_exam_results_for_student(self, exam_id, student_id, school_id):
        """All ExamResult rows for one student (all subjects) for Screen 6."""
        return list(
            ExamResult.objects
            .filter(
                exam_id=exam_id,
                student_id=student_id,
                exam__school_id=school_id,
            )
            .select_related('subject')
            .order_by('subject__subject_name')
        )

    def get_all_exam_results_for_student(self, student_id, school_id):
        """All ExamResult rows for one student across ALL exams."""
        return list(
            ExamResult.objects
            .filter(student_id=student_id, exam__school_id=school_id)
            .select_related('subject', 'exam')
            .order_by('-exam__exam_date')
        )

    def get_student_risks_by_student_id(self, exam_id, student_id, school_id):
        """All StudentRisk rows for one student (all subjects) for Screen 6."""
        risks = StudentRisk.objects.filter(
            exam_id=exam_id,
            student_id=student_id,
            exam__school_id=school_id,
        ).select_related('subject')
        return {r.subject.subject_name: r for r in risks}

    def get_all_student_risks_for_student(self, student_id, school_id):
        """All StudentRisk rows for one student across ALL exams."""
        risks = StudentRisk.objects.filter(
            student_id=student_id, exam__school_id=school_id
        ).select_related('subject', 'exam')
        return {(str(r.exam_id), str(r.subject_id)): r for r in risks}

    # ------------------------------------------------------ Screen 7 queries

    def get_exam_result_for_student_subject(
        self, exam_id, student_id, subject_id, school_id
    ):
        """Single ExamResult for one student × subject for Screen 7."""
        try:
            return ExamResult.objects.select_related('subject').get(
                exam_id=exam_id,
                student_id=student_id,
                exam__school_id=school_id,
                subject_id=subject_id,
            )
        except ExamResult.DoesNotExist:
            return None

    def get_risk_for_student_subject(
        self, exam_id, student_id, subject_id, school_id
    ):
        """Single StudentRisk for one student × subject for Screen 7."""
        try:
            return StudentRisk.objects.select_related('subject').get(
                exam_id=exam_id,
                student_id=student_id,
                exam__school_id=school_id,
                subject_id=subject_id,
            )
        except StudentRisk.DoesNotExist:
            return None

    def get_question_results_by_student_id(
        self, exam_id, student_id, subject_id
    ):
        """QuestionResult rows for one student × subject for Screen 7."""
        return list(
            QuestionResult.objects
            .filter(
                exam_id=exam_id,
                student_id=student_id,
                subject_id=subject_id,
            )
            .order_by('q_no')
        )

    # ------------------------------------------------ legacy ref_id methods

    def get_student_risks_for_exam(self, exam_id, student_ref_id, school_id):
        return list(
            StudentRisk.objects
            .filter(
                exam_id=exam_id,
                student__student_ref_id=student_ref_id,
                student__school_id=school_id,
            )
            .select_related('subject')
        )

    def get_question_results_for_student(
        self, exam_id, student_ref_id, subject_name, school_id
    ):
        return list(
            QuestionResult.objects
            .filter(
                exam_id=exam_id,
                student__student_ref_id=student_ref_id,
                student__school_id=school_id,
                subject__subject_name=subject_name,
            )
            .order_by('q_no')
        )
