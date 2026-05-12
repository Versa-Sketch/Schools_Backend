from rest_framework.response import Response


class ExamPresenter:

    def create_exam_success(self, exam):
        return Response({
            'id': str(exam.id),
            'exam_name': exam.exam_name,
            'analytics_status': exam.analytics_status,
            'academic_class': (
                {'id': str(exam.academic_class_id), 'name': exam.academic_class.name}
                if exam.academic_class_id else None
            ),
            'section': (
                {'id': str(exam.section_id), 'name': exam.section.name}
                if exam.section_id else None
            ),
            'created_at': exam.created_at.isoformat(),
        }, status=201)

    def class_overview_success(self, exam, overview, top_students):
        return Response({
            'exam':         {**self._fmt_exam(exam), 'type': 'CLASS'},
            'class_avgs':   overview['class_avgs'],
            'sections':     overview['sections'],
            'top_students': top_students,
        }, status=200)

    def section_overview_success(self, exam, section, subject_avgs, top_students):
        return Response({
            'exam':         {**self._fmt_exam(exam), 'type': 'SECTION'},
            'section':      {'id': str(section.id), 'name': section.name},
            'subject_avgs': subject_avgs,
            'top_students': top_students,
        }, status=200)

    def _fmt_exam(self, exam):
        return {
            'id':               str(exam.id),
            'exam_name':        exam.exam_name,
            'exam_date':        str(exam.exam_date) if exam.exam_date else None,
            'analytics_status': exam.analytics_status,
        }

    def question_list_success(self, exam, exam_subject, questions):
        return Response({
            'exam': {'id': str(exam.id), 'exam_name': exam.exam_name},
            'subject': {'id': str(exam_subject.id), 'name': exam_subject.subject_name},
            'total_questions': len(questions),
            'questions': [
                {
                    'q_no': q.q_no,
                    'correct_count': q.correct_count,
                    'wrong_count': q.wrong_count,
                    'unattempted_count': q.skip_count,
                    'difficulty_tag': q.difficulty_tag,
                    'difficulty_index': q.difficulty_index,
                    'has_key_error': q.has_key_error,
                }
                for q in questions
            ],
        }, status=200)

    def question_students_success(self, exam, exam_subject, q_no, student_breakdown):
        return Response({
            'exam': {'id': str(exam.id), 'exam_name': exam.exam_name},
            'subject': {'id': str(exam_subject.id), 'name': exam_subject.subject_name},
            'q_no': q_no,
            'students': {
                'correct': student_breakdown.get('C', []),
                'wrong': student_breakdown.get('W', []),
                'unattempted': student_breakdown.get('U', []),
            },
        }, status=200)
