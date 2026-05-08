from core.exceptions import AppException


class AnalyticsValidationError(AppException):
    def __init__(self, details='Validation error'):
        super().__init__(code='ANALYTICS_VALIDATION_ERROR', details=details, status_code=400)


class CSVStructureError(AppException):
    def __init__(self, missing_columns):
        super().__init__(
            code='CSV_STRUCTURE_ERROR',
            details={
                'message': f'{len(missing_columns)} required column(s) are missing from the CSV.',
                'missing_columns': missing_columns,
            },
            status_code=400,
        )


class ExamNotFoundError(AppException):
    def __init__(self):
        super().__init__(code='EXAM_NOT_FOUND', details='Exam not found.', status_code=404)


class StudentNotFoundError(AppException):
    def __init__(self):
        super().__init__(code='STUDENT_NOT_FOUND', details='Student not found.', status_code=404)
