from core.exceptions import NotFoundException, PermissionDeniedException, ValidationException
from teacher import constants
from .base import _ensure_teacher


class CreateAttendanceSessionInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def create_session(self, user, data):
        _ensure_teacher(user)
        teacher = self.storage.get_teacher_profile(user)
        if teacher is None:
            raise NotFoundException('Teacher profile not found.')

        section_id = data.get('section_id')
        date = data.get('date')
        slot = data.get('slot', 'MORNING')

        if not section_id or not date:
            raise ValidationException('section_id and date are required.')
        if slot not in ('MORNING', 'AFTERNOON'):
            raise ValidationException(constants.INVALID_ATTENDANCE_SLOT)
        if not self.storage.is_section_accessible(teacher, section_id):
            raise PermissionDeniedException(constants.SECTION_NOT_ASSIGNED)

        section = self.storage.get_section_by_id(section_id, teacher.school_id)
        if section is None:
            raise NotFoundException('Section not found.')

        config = self.storage.get_school_configuration(teacher.school_id)
        if config and config.attendance_frequency == 'ONCE' and slot == 'AFTERNOON':
            raise ValidationException(constants.INVALID_ATTENDANCE_SLOT)

        session = self.storage.get_or_create_attendance_session(teacher, section, date, slot)
        records = self.storage.get_attendance_records(session.id)
        return self.presenter.attendance_session_success(session=session, records=records)


class MarkAttendanceInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def mark_attendance(self, user, session_id, data):
        _ensure_teacher(user)
        teacher = self.storage.get_teacher_profile(user)
        if teacher is None:
            raise NotFoundException('Teacher profile not found.')

        session = self.storage.get_attendance_session_by_id(session_id, teacher.school_id)
        if session is None:
            raise NotFoundException(constants.ATTENDANCE_SESSION_NOT_FOUND)
        if session.confirmed_at:
            raise ValidationException(constants.ATTENDANCE_ALREADY_CONFIRMED)
        if not self.storage.is_section_accessible(teacher, session.section_id):
            raise PermissionDeniedException(constants.SECTION_NOT_ASSIGNED)

        records_data = data.get('records', [])
        for r in records_data:
            if r.get('status') not in {'PRESENT', 'ABSENT'}:
                raise ValidationException(constants.INVALID_ATTENDANCE_STATUS)

        section_student_ids = set(
            self.storage.get_students_for_section(session.section_id).values_list('id', flat=True)
        )
        for r in records_data:
            if r.get('student_id') not in section_student_ids:
                raise ValidationException(constants.STUDENT_NOT_IN_SECTION)

        saved = self.storage.bulk_set_attendance(session, records_data)
        return self.presenter.attendance_records_success(session_id=session_id, records=saved)


class ConfirmAttendanceInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def confirm_session(self, user, session_id):
        _ensure_teacher(user)
        teacher = self.storage.get_teacher_profile(user)
        if teacher is None:
            raise NotFoundException('Teacher profile not found.')

        session = self.storage.get_attendance_session_by_id(session_id, teacher.school_id)
        if session is None:
            raise NotFoundException(constants.ATTENDANCE_SESSION_NOT_FOUND)
        if session.confirmed_at:
            raise ValidationException(constants.ATTENDANCE_ALREADY_CONFIRMED)
        if not self.storage.is_section_accessible(teacher, session.section_id):
            raise PermissionDeniedException(constants.SECTION_NOT_ASSIGNED)

        session = self.storage.confirm_attendance_session(session)

        notification_count = 0
        config = self.storage.get_school_configuration(teacher.school_id)
        if config and config.whatsapp_absent_automation_enabled:
            notification_count = self.storage.create_absent_notification_logs(
                session=session, school_id=teacher.school_id,
            )

        from core.models import StudentAttendance, ATTENDANCE_STATUS_ABSENT
        absent_count = StudentAttendance.objects.filter(
            session=session, status=ATTENDANCE_STATUS_ABSENT
        ).count()

        from notifications.service import NotificationService
        NotificationService.attendance_confirmed(session.id)
        return self.presenter.confirm_success(
            session=session, absent_count=absent_count, notification_count=notification_count
        )
