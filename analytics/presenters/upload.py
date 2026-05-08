from rest_framework.response import Response


class UploadPresenter:
    def upload_success(self, exam, parse_result):
        return Response(
            {
                'success': True,
                'exam_id': str(exam.id),
                'exam_name': exam.exam_name,
                'exam_date': str(exam.exam_date),
                'analytics_status': exam.analytics_status,
                'students_saved': parse_result.success_count,
                'skipped_count': len(parse_result.skipped),
                'subjects': [
                    {
                        'subject_name': subject_name,
                        'total_questions': len(cols),
                    }
                    for subject_name, cols in parse_result.question_cols.items()
                ],
                'skipped': [
                    {
                        'row_number': e.row_number,
                        'student_id': e.student_id,
                        'reason': e.reason,
                    }
                    for e in parse_result.skipped
                ],
            },
            status=202,
        )
