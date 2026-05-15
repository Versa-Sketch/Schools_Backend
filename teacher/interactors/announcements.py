from django.utils import timezone

from core.exceptions import NotFoundException, PermissionDeniedException, ValidationException
from teacher import constants
from .base import _ensure_teacher


def _parse_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ('1', 'true', 'yes')
    return bool(value)


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


class UpdateTeacherAnnouncementInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def update_announcement(self, user, announcement_id, data, files):
        _ensure_teacher(user)
        teacher = self.storage.get_teacher_profile(user)
        if teacher is None:
            raise NotFoundException('Teacher profile not found.')

        ann = self.storage.get_teacher_announcement(announcement_id, teacher)
        if ann is None:
            raise NotFoundException('Announcement not found.')

        updates = {}
        if 'title' in data:
            title = data['title'].strip()
            if not title:
                raise ValidationException('title cannot be blank.')
            updates['title'] = title
        if 'body' in data:
            body = data['body'].strip()
            if not body:
                raise ValidationException('body cannot be blank.')
            updates['body'] = body
        if 'publish_now' in data:
            updates['published_at'] = timezone.now() if _parse_bool(data['publish_now']) else None

        section = None
        section_id = data.get('section_id')
        if section_id:
            if not self.storage.is_class_teacher(teacher, section_id):
                raise PermissionDeniedException(constants.NOT_CLASS_TEACHER)
            section = self.storage.get_section_by_id(section_id, teacher.school_id)
            if section is None:
                raise NotFoundException('Section not found.')
        else:
            target = ann.announcementtarget_set.first()
            section_id = target.section_id if target else None

        ann = self.storage.update_teacher_announcement(
            announcement=ann,
            section=section,
            updates=updates,
            files=files,
        )
        return self.presenter.announcement_update_success(announcement=ann, section_id=section_id)


class DeleteTeacherAnnouncementInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def delete_announcement(self, user, announcement_id):
        _ensure_teacher(user)
        teacher = self.storage.get_teacher_profile(user)
        if teacher is None:
            raise NotFoundException('Teacher profile not found.')

        ann = self.storage.get_teacher_announcement(announcement_id, teacher)
        if ann is None:
            raise NotFoundException('Announcement not found.')

        self.storage.delete_teacher_announcement(announcement=ann)
        return self.presenter.announcement_delete_success()
