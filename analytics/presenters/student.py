from collections import defaultdict

from rest_framework.response import Response

_RISK_PRIORITY = {'ALERT': 3, 'WATCH': 2, 'SAFE': 1}


class StudentPresenter:

    def student_no_exams_success(self):
        return Response({'success': True, 'exams': [], 'message': 'Student has not written any exam yet.'}, status=200)

    # ------------------------------------------------------------ Screen 6

    def student_summary_success(
        self, student, exam, exams, exam_results, risk_map, rank_details=None
    ):
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
                'subject_id':         str(er.subject_id),
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
            **self._fmt_rank_details(rank_details),
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

    # ------------------------------------------------------------ All Exams

    def student_all_exams_success(
        self, student, exams, all_results, all_risks, rank_details_map=None
    ):
        exam_data_map = {
            str(exam.id): {
                'id': str(exam.id),
                'exam_name': exam.exam_name,
                'exam_date': str(exam.exam_date) if exam.exam_date else None,
                **self._fmt_rank_details((rank_details_map or {}).get(str(exam.id))),
                'overall_risk': 'SAFE',
                'subjects': [],
            }
            for exam in exams
        }

        for er in all_results:
            eid = str(er.exam_id)
            if eid not in exam_data_map:
                continue

            subj = er.subject
            risk = all_risks.get((eid, str(subj.id)))
            risk_label = risk.risk_label if risk else 'SAFE'

            exam_data_map[eid]['subjects'].append({
                'subject_id': str(subj.id),
                'subject_name': subj.subject_name,
                'marks': er.total_marks,
                'max_marks': subj.max_marks,
                'risk_label': risk_label,
            })

            # Update overall risk
            current_overall = exam_data_map[eid]['overall_risk']
            if _RISK_PRIORITY.get(risk_label, 1) > _RISK_PRIORITY.get(current_overall, 1):
                exam_data_map[eid]['overall_risk'] = risk_label

        # Filter to only exams that have results (or return all, but we probably just want the mapped list)
        exam_list = [exam_data_map[str(e.id)] for e in exams]

        return Response({
            'success': True,
            'student': self._fmt_student(student),
            'exams': exam_list,
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
            'exam_date': str(exam.exam_date) if exam.exam_date else None,
        }

    def _fmt_rank_details(self, details):
        details = details or {}
        exam_total_marks = details.get('exam_total_marks', 0)
        exam_max_marks = details.get('exam_max_marks', 0)
        exam_percentage = details.get('exam_percentage', 0)
        return {
            'total_marks': exam_total_marks,
            'max_marks': exam_max_marks,
            'percentage': exam_percentage,
            'exam_total_marks': exam_total_marks,
            'exam_max_marks': exam_max_marks,
            'exam_percentage': exam_percentage,
            'class_rank': details.get('class_rank'),
            'section_rank': details.get('section_rank'),
        }

    def _fmt_exam_summary(self, exam):
        return {
            'id':               str(exam.id),
            'exam_name':        exam.exam_name,
            'exam_date':        str(exam.exam_date) if exam.exam_date else None,
            'analytics_status': exam.analytics_status,
        }

    # ------------------------------------------------------------ Student exam screens

    def exam_list_success(self, exams):
        return Response({
            'count': len(exams),
            'exams': [self._fmt_exam_summary(e) for e in exams],
        }, status=200)

    def exam_subjects_success(self, exam, exam_results):
        subjects = []
        for er in exam_results:
            mm = er.subject.max_marks or 1
            subjects.append({
                'subject_id': str(er.subject_id),
                'subject_name': er.subject.subject_name,
                'total_marks': er.total_marks,
                'max_marks': mm,
                'percentage': round((er.total_marks / mm) * 100, 1),
                'correct': er.correct,
                'wrong': er.wrong,
                'unattempted': er.unattempted,
                'exam_rank': er.exam_rank,
            })
        return Response({
            'exam': self._fmt_exam(exam),
            'subjects': subjects,
        }, status=200)

    def subject_questions_success(self, exam, exam_subject, question_results):
        return Response({
            'exam': self._fmt_exam(exam),
            'subject': {'id': str(exam_subject.id), 'name': exam_subject.subject_name},
            'questions': [
                {'q_no': qr.q_no, 'status': qr.status}
                for qr in question_results
            ],
        }, status=200)
