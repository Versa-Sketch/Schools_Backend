from core.exceptions import NotFoundException, PermissionDeniedException, ValidationException
from django.utils.dateparse import parse_datetime
from teacher import constants
from .base import _ensure_teacher


class CreateHomeworkInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def create_homework(self, user, data):
        _ensure_teacher(user)
        teacher = self.storage.get_teacher_profile(user)
        if teacher is None:
            raise NotFoundException('Teacher profile not found.')

        section_id = data.get('section_id')
        subject_id = data.get('subject_id')
        description = data.get('description', '').strip()
        deadline = data.get('deadline')

        if not all([section_id, subject_id, description, deadline]):
            raise ValidationException('section_id, subject_id, description, and deadline are required.')

        parsed_deadline = parse_datetime(deadline)
        if parsed_deadline is None:
            raise ValidationException('Invalid deadline format.')
        deadline = parsed_deadline
        if not self.storage.is_section_accessible(teacher, section_id):
            raise PermissionDeniedException(constants.SECTION_NOT_ASSIGNED)

        section = self.storage.get_section_by_id(section_id, teacher.school_id)
        if section is None:
            raise NotFoundException('Section not found.')
        subject = self.storage.get_subject_by_id(subject_id, teacher.school_id)
        if subject is None:
            raise ValidationException(constants.SUBJECT_NOT_ASSIGNED)

        hw = self.storage.create_homework(teacher, section, subject, description, deadline)
        from notifications.service import NotificationService
        NotificationService.homework_assigned(hw.id)
        return self.presenter.homework_success(homework=hw)


class ListHomeworkInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def list_homework(self, user, section_id=None, subject_id=None, deadline_from=None, deadline_to=None):
        _ensure_teacher(user)
        teacher = self.storage.get_teacher_profile(user)
        if teacher is None:
            raise NotFoundException('Teacher profile not found.')
        homework = self.storage.get_homework(teacher, section_id, subject_id, deadline_from, deadline_to)
        return self.presenter.homework_list_success(homework=homework)
