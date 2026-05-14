from core.exceptions import NotFoundException, PermissionDeniedException, ValidationException
from analytics.constants import ANALYTICS_STATUS_DONE
from analytics.exceptions import AnalyticsValidationError, ExamNotFoundError
from principal.exceptions import PrincipalPermissionException


class CreateExamInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def create(self, user, data):
        if user.role not in ('ADMIN', 'PRINCIPAL'):
            raise PrincipalPermissionException()
        profile = self.storage.get_principal_profile(user)
        if profile is None:
            raise NotFoundException('Principal profile not found.')

        exam_name = data.get('exam_name', '').strip()
        class_id = data.get('class_id') or None
        section_id = data.get('section_id') or None

        if not exam_name:
            raise ValidationException('exam_name is required.')
        if not class_id and not section_id:
            raise ValidationException('Either class_id or section_id is required.')
        if class_id and section_id:
            raise ValidationException('Provide either class_id or section_id, not both.')

        exam = self.storage.create_exam_record(
            school=profile.school,
            exam_name=exam_name,
            class_id=class_id,
            section_id=section_id,
        )
        return self.presenter.create_exam_success(exam)


class ListExamsInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def list(self, user, class_id=None):
        # Fetch profile once — used for school_id resolution and data query
        profile = None
        school_id = getattr(user, 'school_id', None)
        if not school_id:
            if user.role in ('ADMIN', 'PRINCIPAL'):
                profile = self.storage.get_principal_profile(user)
                school_id = profile.school_id if profile else None
            elif user.role == 'TEACHER':
                profile = self.storage.get_teacher_profile(user)
                school_id = profile.school_id if profile else None
            elif user.role == 'STUDENT':
                profile = self.storage.get_student_profile(user)
                school_id = profile.school_id if profile else None

        if not school_id:
            return self.presenter.permission_denied()

        if class_id and user.role in ('ADMIN', 'PRINCIPAL', 'TEACHER'):
            if user.role in ('ADMIN', 'PRINCIPAL'):
                exams = self.storage.get_exams_for_class(class_id, school_id)
            else:
                teacher_profile = profile or self.storage.get_teacher_profile(user)
                if not teacher_profile:
                    return self.presenter.permission_denied()
                all_exams = self.storage.get_exams_for_teacher(teacher_profile, school_id)
                exams = [e for e in all_exams if str(e.academic_class_id) == str(class_id)]

            exam_ids = [str(e.id) for e in exams]
            if exam_ids:
                section_analytics = self.storage.get_section_analytics_for_exam_list(
                    exam_ids, class_id, school_id
                )
                student_counts = self.storage.get_student_counts_for_class_exams(
                    exam_ids, class_id, school_id
                )
            else:
                section_analytics, student_counts = {}, {}

            return self.presenter.exam_list_with_sections_success(
                exams, section_analytics, student_counts
            )

        if user.role == 'STUDENT':
            student_profile = profile or self.storage.get_student_profile(user)
            if not student_profile:
                return self.presenter.permission_denied()
            exams = self.storage.get_exams_for_student(student_profile.id, school_id)
        elif user.role == 'TEACHER':
            teacher_profile = profile or self.storage.get_teacher_profile(user)
            if not teacher_profile:
                return self.presenter.permission_denied()
            exams = self.storage.get_exams_for_teacher(teacher_profile, school_id)
        elif user.role in ('PRINCIPAL', 'ADMIN'):
            exams = self.storage.get_exams_for_school(school_id)
        else:
            return self.presenter.permission_denied()

        class_ids = [e.academic_class_id for e in exams if e.academic_class_id]
        sections_by_class = {}
        if class_ids:
            for s in self.storage.get_sections_for_class_ids(class_ids, school_id):
                sections_by_class.setdefault(str(s.academic_class_id), []).append(s)

        if user.role == 'TEACHER':
            assigned_sections = list(teacher_profile.assigned_sections.all())
            return self.presenter.exam_list_success(exams, sections_by_class=sections_by_class, teacher_sections=assigned_sections)
        return self.presenter.exam_list_success(exams, sections_by_class=sections_by_class)


class ExamOverviewInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def overview(self, user, exam_id):
        school_id = getattr(user, 'school_id', None)
        if not school_id:
            if user.role in ('ADMIN', 'PRINCIPAL'):
                profile = self.storage.get_principal_profile(user)
                school_id = profile.school_id if profile else None
            elif user.role == 'TEACHER':
                profile = self.storage.get_teacher_profile(user)
                school_id = profile.school_id if profile else None
            elif user.role == 'STUDENT':
                profile = self.storage.get_student_profile(user)
                school_id = profile.school_id if profile else None

        if not school_id:
            return self.presenter.permission_denied()

        exam = self.storage.get_exam_by_id(exam_id, school_id)
        if exam is None:
            raise ExamNotFoundError()
        if exam.analytics_status != ANALYTICS_STATUS_DONE:
            raise AnalyticsValidationError(
                f'Analytics not ready (status: {exam.analytics_status}).'
            )

        if user.role in ('ADMIN', 'PRINCIPAL'):
            top_students = self.storage.get_top_students(exam_id, n=5)
            if exam.academic_class_id:
                overview = self.storage.get_exam_overview(exam_id, school_id)
                return self.presenter.class_overview_success(exam, overview, top_students, role_view='STAFF')
            else:
                subject_avgs = self.storage.get_section_overview(exam_id, exam.section_id)
                return self.presenter.section_overview_success(exam, exam.section, subject_avgs, top_students, role_view='STAFF')

        elif user.role == 'TEACHER':
            teacher_profile = self.storage.get_teacher_profile(user)
            if not teacher_profile:
                raise NotFoundException('Teacher profile not found.')
            assigned_sections = list(teacher_profile.assigned_sections.all())
            
            top_students = self.storage.get_top_students(exam_id, n=5)
            if exam.academic_class_id:
                overview = self.storage.get_exam_overview(exam_id, school_id)
                return self.presenter.class_overview_success(exam, overview, top_students, role_view='STAFF', teacher_sections=assigned_sections)
            else:
                subject_avgs = self.storage.get_section_overview(exam_id, exam.section_id)
                return self.presenter.section_overview_success(exam, exam.section, subject_avgs, top_students, role_view='STAFF')

        elif user.role == 'STUDENT':
            student_profile = self.storage.get_student_profile(user)
            if not student_profile:
                raise NotFoundException('Student profile not found.')
            
            student_results = self.storage.get_exam_results_for_student(exam_id, student_profile.id, school_id)
            student_risks = self.storage.get_student_risks_by_student_id(exam_id, student_profile.id, school_id)
            return self.presenter.student_overview_success(exam, student_results, student_risks)

        else:
            return self.presenter.permission_denied()


class ClassSubjectQuestionsInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def get(self, user, exam_id, subject_id):
        if user.role in ('ADMIN', 'PRINCIPAL'):
            profile = self.storage.get_principal_profile(user)
            if profile is None:
                raise NotFoundException('Principal profile not found.')
            school_id = profile.school_id
        elif user.role == 'TEACHER':
            teacher = getattr(user, 'teacherprofile', None)
            if teacher is None:
                raise NotFoundException('Teacher profile not found.')
            school_id = teacher.school_id
        else:
            raise PrincipalPermissionException()

        exam = self.storage.get_exam_by_id(exam_id, school_id)
        if exam is None:
            raise ExamNotFoundError()
        if exam.analytics_status != ANALYTICS_STATUS_DONE:
            raise AnalyticsValidationError(
                f'Analytics not ready (status: {exam.analytics_status}).'
            )

        exam_subject = self.storage.get_exam_subject_by_id(subject_id, exam_id)
        if exam_subject is None:
            raise NotFoundException('Subject not found for this exam.')

        questions = self.storage.get_question_analytics_for_subject(exam_id, subject_id)
        return self.presenter.question_list_success(exam, exam_subject, questions)


class ClassQuestionStudentsInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def get(self, user, exam_id, subject_id, q_no):
        if user.role in ('ADMIN', 'PRINCIPAL'):
            profile = self.storage.get_principal_profile(user)
            if profile is None:
                raise NotFoundException('Principal profile not found.')
            school_id = profile.school_id
        elif user.role == 'TEACHER':
            teacher = getattr(user, 'teacherprofile', None)
            if teacher is None:
                raise NotFoundException('Teacher profile not found.')
            school_id = teacher.school_id
        else:
            raise PrincipalPermissionException()

        exam = self.storage.get_exam_by_id(exam_id, school_id)
        if exam is None:
            raise ExamNotFoundError()
        if exam.analytics_status != ANALYTICS_STATUS_DONE:
            raise AnalyticsValidationError(
                f'Analytics not ready (status: {exam.analytics_status}).'
            )

        exam_subject = self.storage.get_exam_subject_by_id(subject_id, exam_id)
        if exam_subject is None:
            raise NotFoundException('Subject not found for this exam.')

        student_breakdown = self.storage.get_class_question_students(exam_id, subject_id, q_no)
        return self.presenter.question_students_success(exam, exam_subject, q_no, student_breakdown)


class SectionDetailInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def get(self, user, exam_id, section_id):
        if user.role in ('ADMIN', 'PRINCIPAL'):
            profile = self.storage.get_principal_profile(user)
            if profile is None:
                raise NotFoundException('Principal profile not found.')
            school_id = profile.school_id
        elif user.role == 'TEACHER':
            teacher = getattr(user, 'teacherprofile', None)
            if teacher is None:
                raise NotFoundException('Teacher profile not found.')
            school_id = teacher.school_id
            assigned_ids = list(teacher.assigned_sections.values_list('id', flat=True))
            if section_id not in assigned_ids:
                raise PermissionDeniedException('You can only view sections assigned to you.')
        else:
            raise PrincipalPermissionException()

        exam = self.storage.get_exam_by_id(exam_id, school_id)
        if exam is None:
            raise ExamNotFoundError()
        if exam.analytics_status != ANALYTICS_STATUS_DONE:
            raise AnalyticsValidationError(
                f'Analytics not ready (status: {exam.analytics_status}).'
            )

        section = self.storage.get_section_by_id(section_id, school_id)
        if section is None:
            raise NotFoundException('Section not found.')

        subjects_with_delta = self.storage.get_section_subject_detail(exam_id, section_id, school_id)
        return self.presenter.section_detail_success(section, exam, subjects_with_delta)


class SectionSubjectQuestionsInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def get(self, user, exam_id, section_id, subject_id):
        if user.role in ('ADMIN', 'PRINCIPAL'):
            profile = self.storage.get_principal_profile(user)
            if profile is None:
                raise NotFoundException('Principal profile not found.')
            school_id = profile.school_id
        elif user.role == 'TEACHER':
            teacher = getattr(user, 'teacherprofile', None)
            if teacher is None:
                raise NotFoundException('Teacher profile not found.')
            school_id = teacher.school_id
            assigned_ids = list(teacher.assigned_sections.values_list('id', flat=True))
            if section_id not in assigned_ids:
                raise PermissionDeniedException('You can only view sections assigned to you.')
        else:
            raise PrincipalPermissionException()

        exam = self.storage.get_exam_by_id(exam_id, school_id)
        if exam is None:
            raise ExamNotFoundError()
        if exam.analytics_status != ANALYTICS_STATUS_DONE:
            raise AnalyticsValidationError(
                f'Analytics not ready (status: {exam.analytics_status}).'
            )

        section = self.storage.get_section_by_id(section_id, school_id)
        if section is None:
            raise NotFoundException('Section not found.')

        exam_subject = self.storage.get_exam_subject_by_id(subject_id, exam_id)
        if exam_subject is None:
            raise NotFoundException('Subject not found for this exam.')

        questions = self.storage.get_question_analytics_for_subject(exam_id, subject_id)
        return self.presenter.section_subject_questions_success(section, exam, exam_subject, questions)


class SectionQuestionStudentsInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def get(self, user, exam_id, section_id, subject_id, q_no):
        if user.role in ('ADMIN', 'PRINCIPAL'):
            profile = self.storage.get_principal_profile(user)
            if profile is None:
                raise NotFoundException('Principal profile not found.')
            school_id = profile.school_id
        elif user.role == 'TEACHER':
            teacher = getattr(user, 'teacherprofile', None)
            if teacher is None:
                raise NotFoundException('Teacher profile not found.')
            school_id = teacher.school_id
            assigned_ids = list(teacher.assigned_sections.values_list('id', flat=True))
            if section_id not in assigned_ids:
                raise PermissionDeniedException('You can only view sections assigned to you.')
        else:
            raise PrincipalPermissionException()

        exam = self.storage.get_exam_by_id(exam_id, school_id)
        if exam is None:
            raise ExamNotFoundError()
        if exam.analytics_status != ANALYTICS_STATUS_DONE:
            raise AnalyticsValidationError(
                f'Analytics not ready (status: {exam.analytics_status}).'
            )

        section = self.storage.get_section_by_id(section_id, school_id)
        if section is None:
            raise NotFoundException('Section not found.')

        exam_subject = self.storage.get_exam_subject_by_id(subject_id, exam_id)
        if exam_subject is None:
            raise NotFoundException('Subject not found for this exam.')

        student_breakdown = self.storage.get_question_results_for_section_question(
            exam_id, section_id, subject_id, q_no
        )
        return self.presenter.section_question_students_success(
            section, exam, exam_subject, q_no, student_breakdown
        )
