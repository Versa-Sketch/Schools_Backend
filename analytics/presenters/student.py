from collections import defaultdict

from rest_framework.response import Response

_RISK_PRIORITY = {'ALERT': 3, 'WATCH': 2, 'SAFE': 1}


class StudentPresenter:

    # ------------------------------------------------------------ Screen 6

    def student_summary_success(self, student, exam, exams, exam_results, risk_map):
        """
        risk_map: dict keyed by subject_name → StudentRisk instance
        exam_results: list of ExamResult (one per subject)
        """
        max_marks = {es.subject_name: es.max_marks for es in exam.subjects.all()}

        subjects = []
        risk_labels = []

        for er in exam_results:
            subj = er.subject.subject_name
            mm = max_marks.get(subj, 1)
            pct = round((er.total_marks / mm) * 100, 1) if mm else 0

            risk = risk_map.get(subj)
            risk_label = risk.risk_label if risk else 'SAFE'
            perf_label = risk.performance_label if risk else None
            z_score = round(risk.z_score, 4) if risk else None

            risk_labels.append(risk_label)

            subjects.append({
                'subject_name':       subj,
                'total_marks':        er.total_marks,
                'max_marks':          mm,
                'percentage':         pct,
                'exam_rank':          er.exam_rank,
                'correct':            er.correct,
                'wrong':              er.wrong,
                'unattempted':        er.unattempted,
                'risk_label':         risk_label,
                'performance_label':  perf_label,
                'z_score':            z_score,
            })

        # Overall risk = worst across all subjects
        overall_risk = max(
            risk_labels,
            key=lambda lbl: _RISK_PRIORITY.get(lbl, 0),
            default='SAFE',
        )

        return Response({
            'success':      True,
            'student':      self._fmt_student(student),
            'exam':         self._fmt_exam(exam),
            'exams':        [self._fmt_exam_summary(e) for e in exams],
            'subjects':     subjects,
            'overall_risk': overall_risk,
        }, status=200)

    # ------------------------------------------------------------ Screen 7

    def student_subject_success(
        self, student, exam, subject_name, exam_result, risk, question_results
    ):
        mm = exam_result.subject.max_marks
        pct = round((exam_result.total_marks / mm) * 100, 1) if mm else 0

        return Response({
            'success':      True,
            'student':      self._fmt_student(student),
            'exam':         self._fmt_exam(exam),
            'subject_name': subject_name,
            'result': {
                'total_marks':       exam_result.total_marks,
                'max_marks':         mm,
                'percentage':        pct,
                'exam_rank':         exam_result.exam_rank,
                'correct':           exam_result.correct,
                'wrong':             exam_result.wrong,
                'unattempted':       exam_result.unattempted,
                'risk_label':        risk.risk_label if risk else 'SAFE',
                'performance_label': risk.performance_label if risk else None,
                'z_score':           round(risk.z_score, 4) if risk else None,
            },
            'questions': [
                {'q_no': qr.q_no, 'status': qr.status}
                for qr in question_results
            ],
        }, status=200)

    # ------------------------------------------------------------ shared

    def _fmt_student(self, student):
        return {
            'student_id':     str(student.id),
            'student_ref_id': student.student_ref_id,
            'name':           student.name,
            'class_name':     student.class_name,
            'section_name':   student.section_name,
        }

    def _fmt_exam(self, exam):
        return {
            'id':        str(exam.id),
            'exam_name': exam.exam_name,
            'exam_date': str(exam.exam_date),
        }

    def _fmt_exam_summary(self, exam):
        return {
            'id':               str(exam.id),
            'exam_name':        exam.exam_name,
            'exam_date':        str(exam.exam_date),
            'analytics_status': exam.analytics_status,
        }
