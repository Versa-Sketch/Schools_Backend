from core.exceptions import NotFoundException, PermissionDeniedException, ValidationException
from teacher import constants
from .base import _ensure_teacher


class CreateTeacherAnnouncementInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def create_announcement(self, user, data, files):
        _ensure_teacher(user)
        teacher = self.storage.get_teacher_profile(user)
        if teacher is None:
            raise NotFoundException('Teacher profile not found.')

        section_id = data.get('section_id')
        title = data.get('title', '').strip()
        body = data.get('body', '').strip()
        publish_now = data.get('publish_now', True)

        if not section_id:
            raise ValidationException('section_id is required.')
        if not title:
            raise ValidationException('title is required.')
        if not body:
            raise ValidationException('body is required.')
        if not self.storage.is_class_teacher(teacher, section_id):
            raise PermissionDeniedException(constants.NOT_CLASS_TEACHER)

        section = self.storage.get_section_by_id(section_id, teacher.school_id)
        if section is None:
            raise NotFoundException('Section not found.')

        ann = self.storage.create_teacher_announcement(teacher, section, title, body, files, publish_now)
        from notifications.service import NotificationService
        NotificationService.announcement_published(ann)
        return self.presenter.announcement_success(announcement=ann, section_id=section_id)
