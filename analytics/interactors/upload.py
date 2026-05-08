import threading

from django.db import transaction

from core.exceptions import NotFoundException
from analytics.exceptions import AnalyticsValidationError
from analytics.models import ExamResult, QuestionResult
from analytics.services.csv_parser import parse_file
from principal.exceptions import PrincipalPermissionException


class UploadExamCSVInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def upload(self, user, csv_file):
        if user.role not in ('ADMIN', 'PRINCIPAL'):
            raise PrincipalPermissionException()

        profile = self.storage.get_principal_profile(user)
        if profile is None:
            raise NotFoundException('Principal profile not found.')
        school = profile.school

        if csv_file is None:
            raise AnalyticsValidationError('csv_file is required.')

        # Raises CSVStructureError or AnalyticsValidationError on bad input.
        # Both are caught by the global exception handler and returned as 400s.
        parse_result = parse_file(csv_file)

        if parse_result.success_count == 0:
            raise AnalyticsValidationError(
                f'No valid student rows found. '
                f'{len(parse_result.skipped)} row(s) had errors.'
            )

        with transaction.atomic():
            exam = self.storage.create_exam(
                school=school,
                exam_name=parse_result.exam_meta.exam_name,
                exam_date=parse_result.exam_meta.exam_date,
                uploaded_by=user,
            )

            exam_subjects = {}
            for subject_name, cols in parse_result.question_cols.items():
                core_subject = self.storage.get_or_create_core_subject(school, subject_name)
                exam_subjects[subject_name] = self.storage.create_exam_subject(
                    exam=exam,
                    subject_name=subject_name,
                    total_questions=len(cols),
                    max_marks=len(cols),
                    core_subject=core_subject,
                )

            exam_result_objs     = []
            question_result_objs = []

            for parsed_row in parse_result.rows:
                student = self.storage.get_or_create_analytics_student(
                    school=school,
                    student_ref_id=parsed_row.student.student_ref_id,
                    name=parsed_row.student.name,
                    class_name=parsed_row.student.class_name,
                    section_name=parsed_row.student.section_name,
                )

                for subject_name, exam_subject in exam_subjects.items():
                    sr = parsed_row.results[subject_name]
                    exam_result_objs.append(ExamResult(
                        exam=exam,
                        student=student,
                        subject=exam_subject,
                        total_marks=sr.total_marks,
                        exam_rank=sr.rank,
                        correct=sr.correct,
                        wrong=sr.wrong,
                        unattempted=sr.unattempted,
                    ))

                    for q_no, status in parsed_row.question_statuses[subject_name].items():
                        question_result_objs.append(QuestionResult(
                            exam=exam,
                            student=student,
                            subject=exam_subject,
                            q_no=q_no,
                            status=status,
                        ))

            self.storage.bulk_create_exam_results(exam_result_objs)
            self.storage.bulk_create_question_results(question_result_objs)

        # Start background analytics AFTER the transaction commits so all
        # rows are visible to the thread's DB queries.
        threading.Thread(
            target=self.storage.run_analytics,
            args=(str(exam.id),),
            daemon=True,
        ).start()

        return self.presenter.upload_success(exam=exam, parse_result=parse_result)
