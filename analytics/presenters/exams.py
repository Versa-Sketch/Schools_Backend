from rest_framework.response import Response


class ExamPresenter:

    def permission_denied(self):
        return Response({'success': False, 'details': 'Permission denied.'}, status=403)

    def exam_list_success(self, exams):
        return Response({
            'success': True,
            'exams': [
                {**self._fmt_exam(exam), 'type': 'CLASS' if exam.academic_class_id else 'SECTION'}
                for exam in exams
            ]
        }, status=200)

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

    def class_overview_success(self, exam, overview, top_students, role_view='STAFF', teacher_sections=None):
        sections = overview['sections']
        if teacher_sections is not None:
            assigned_ids = {str(s.id) for s in teacher_sections}
            sections = [s for s in sections if s['section_id'] in assigned_ids]

        return Response({
            'exam':         {**self._fmt_exam(exam), 'type': 'CLASS'},
            'role_view':    role_view,
            'class_avgs':   overview['class_avgs'],
            'sections':     sections,
            'top_students': top_students,
        }, status=200)

    def section_overview_success(self, exam, section, subject_avgs, top_students, role_view='STAFF'):
        return Response({
            'exam':         {**self._fmt_exam(exam), 'type': 'SECTION'},
            'role_view':    role_view,
            'section':      {'id': str(section.id), 'name': section.name},
            'subject_avgs': subject_avgs,
            'top_students': top_students,
        }, status=200)

    def student_overview_success(self, exam, student_results, student_risks):
        subjects = []
        total_marks = 0
        overall_risk = 'SAFE'
        risk_priority = {'ALERT': 3, 'WATCH': 2, 'SAFE': 1}
        
        for r in student_results:
            total_marks += r.total_marks
            risk = student_risks.get(r.subject.subject_name)
            risk_label = risk.risk_label if risk else 'SAFE'
            
            if risk_priority.get(risk_label, 1) > risk_priority.get(overall_risk, 1):
                overall_risk = risk_label
                
            subjects.append({
                'subject_id': str(r.subject.id),
                'subject_name': r.subject.subject_name,
                'total_marks': r.total_marks,
                'max_marks': r.subject.max_marks,
                'correct': r.correct,
                'wrong': r.wrong,
                'unattempted': r.unattempted,
                'risk_label': risk_label,
            })
            
        return Response({
            'exam': {**self._fmt_exam(exam), 'type': 'CLASS' if exam.academic_class_id else 'SECTION'},
            'role_view': 'STUDENT',
            'student_results': {
                'total_marks': total_marks,
                'overall_risk': overall_risk,
                'subjects': subjects,
            }
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
