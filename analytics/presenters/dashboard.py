from collections import defaultdict

from rest_framework.response import Response

_STATUS_MESSAGES = {
    'PENDING': 'Analytics is queued. Please try again in a moment.',
    'RUNNING': 'Analytics is processing. Please try again shortly.',
    'FAILED':  'Analytics computation failed. Please re-upload the CSV.',
}


class DashboardPresenter:

    # ------------------------------------------------------------ Screen 1

    def exams_only(self, exams):
        return Response({
            'success': True,
            'exams': [self._fmt_exam_summary(e) for e in exams],
        }, status=200)

    def exam_not_ready(self, exam, exams):
        return Response({
            'success': True,
            'exam': {
                'id':               str(exam.id),
                'exam_name':        exam.exam_name,
                'analytics_status': exam.analytics_status,
            },
            'message': _STATUS_MESSAGES.get(exam.analytics_status, 'Analytics not ready.'),
            'exams': [self._fmt_exam_summary(e) for e in exams],
        }, status=200)

    def dashboard_success(self, exam, exams, section_analytics, subject_stats):
        return Response({
            'success': True,
            'exam': self._fmt_exam_detail(exam),
            'subject_summary':  [self._fmt_subject_stat(s) for s in subject_stats],
            'class_comparison': self._build_class_comparison(section_analytics),
            'exams': [self._fmt_exam_summary(e) for e in exams],
        }, status=200)

    # ------------------------------------------------------------ Screen 2

    def class_detail_success(self, class_name, exam, section_analytics, student_counts):
        return Response({
            'success':    True,
            'class_name': class_name,
            'exam': {
                'id':        str(exam.id),
                'exam_name': exam.exam_name,
                'exam_date': str(exam.exam_date),
            },
            'sections': self._build_sections(section_analytics, student_counts),
        }, status=200)

    # ------------------------------------------------------------ formatters

    def _fmt_exam_summary(self, exam):
        return {
            'id':               str(exam.id),
            'exam_name':        exam.exam_name,
            'exam_date':        str(exam.exam_date),
            'analytics_status': exam.analytics_status,
        }

    def _fmt_exam_detail(self, exam):
        return {
            'id':               str(exam.id),
            'exam_name':        exam.exam_name,
            'exam_date':        str(exam.exam_date),
            'analytics_status': exam.analytics_status,
        }

    def _fmt_subject_stat(self, stat):
        return {
            'subject_name':    stat['subject_name'],
            'total_questions': stat['total_questions'],
            'school_avg':      stat['school_avg'],
            'top_scorer':      stat['top_scorer'],
        }

    # --------------------------------------------------------- class comparison chart

    def _build_class_comparison(self, section_analytics):
        """
        Group section averages by (class, subject) and average them.
        Returns the chart-ready dict:
          {"labels": ["Class 11", ...], "datasets": [{"subject": "MATHS", "data": [51.9, ...]}, ...]}
        """
        by_class_subject = defaultdict(lambda: defaultdict(list))
        for sa in section_analytics:
            by_class_subject[sa.academic_class.name][sa.subject.subject_name].append(sa.avg_marks)

        classes  = sorted(by_class_subject.keys())
        subjects = sorted({sa.subject.subject_name for sa in section_analytics})

        datasets = []
        for subject in subjects:
            data = []
            for cls in classes:
                marks_list = by_class_subject[cls][subject]
                avg = round(sum(marks_list) / len(marks_list), 2) if marks_list else 0
                data.append(avg)
            datasets.append({'subject': subject, 'data': data})

        return {'labels': classes, 'datasets': datasets}

    # --------------------------------------------------------- section breakdown

    def _build_sections(self, section_analytics, student_counts):
        """
        Group SectionAnalytics rows by section, return ordered list of sections
        each containing a subjects list.
        """
        by_section  = defaultdict(list)
        section_meta = {}

        for sa in section_analytics:
            sid = str(sa.section_id)
            by_section[sid].append(sa)
            section_meta[sid] = sa.section.name

        result = []
        for sid, name in sorted(section_meta.items(), key=lambda x: x[1]):
            subjects = [
                self._fmt_section_analytics(sa)
                for sa in sorted(by_section[sid], key=lambda s: s.subject.subject_name)
            ]
            result.append({
                'section_id':    sid,
                'section_name':  name,
                'student_count': student_counts.get(sid, 0),
                'subjects':      subjects,
            })
        return result

    def _fmt_section_analytics(self, sa):
        top_scorer = None
        if sa.top_scorer:
            top_scorer = {
                'name':           sa.top_scorer.name,
                'student_ref_id': sa.top_scorer.student_ref_id,
                'marks':          getattr(sa, '_top_marks', None),
            }
        return {
            'subject_name':   sa.subject.subject_name,
            'avg_marks':      sa.avg_marks,
            'median_marks':   sa.median_marks,
            'std_dev':        sa.std_dev,
            'at_risk_count':  sa.at_risk_count,
            'top_scorer':     top_scorer,
        }
