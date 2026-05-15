from django.utils import timezone

from core.exceptions import NotFoundException, ValidationException
from principal import constants
from .base import _ensure_principal


def _parse_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ('1', 'true', 'yes')
    return bool(value)


class CreateAnnouncementInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def create_announcement(self, user, data, files):
        _ensure_principal(user)
        profile = self.storage.get_principal_profile(user)
        if profile is None:
            raise NotFoundException('Principal profile not found.')
        school = profile.school

        title = data.get('title', '').strip()
        body = data.get('body', '').strip()
        audience = data.get('audience', '').strip()
        publish_now = data.get('publish_now', True)
        class_ids = data.getlist('class_ids') if hasattr(data, 'getlist') else data.get('class_ids', [])
        section_ids = data.getlist('section_ids') if hasattr(data, 'getlist') else data.get('section_ids', [])

        if not title:
            raise ValidationException('title is required.')
        if not body:
            raise ValidationException('body is required.')
        if audience not in ('SCHOOL', 'CLASS', 'SECTION'):
            raise ValidationException(constants.INVALID_AUDIENCE)
        if audience == 'CLASS' and not class_ids:
            raise ValidationException('class_ids are required for CLASS audience.')
        if audience == 'SECTION' and not section_ids:
            raise ValidationException('section_ids are required for SECTION audience.')

        if class_ids:
            found = self.storage.get_classes_by_ids(class_ids, school.id)
            if len(found) != len(class_ids):
                raise ValidationException(constants.CLASS_NOT_FOUND)
        if section_ids:
            found = self.storage.get_sections_by_ids(section_ids, school.id)
            if len(found) != len(section_ids):
                raise ValidationException(constants.SECTION_NOT_FOUND)

        ann = self.storage.create_announcement(
            school=school, author=user, title=title, body=body,
            audience=audience, class_ids=class_ids, section_ids=section_ids,
            files=files, publish_now=publish_now,
        )
        from notifications.service import NotificationService
        NotificationService.announcement_published(ann)
        return self.presenter.announcement_success(announcement=ann)


class UpdateAnnouncementInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def update_announcement(self, user, announcement_id, data, files):
        _ensure_principal(user)
        profile = self.storage.get_principal_profile(user)
        if profile is None:
            raise NotFoundException('Principal profile not found.')

        ann = self.storage.get_announcement(announcement_id=announcement_id, school_id=profile.school_id)
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
        if 'audience' in data:
            audience = data['audience'].strip()
            if audience not in ('SCHOOL', 'CLASS', 'SECTION'):
                raise ValidationException(constants.INVALID_AUDIENCE)
            updates['audience'] = audience
        if 'publish_now' in data:
            updates['published_at'] = timezone.now() if _parse_bool(data['publish_now']) else None

        if 'class_ids' in data:
            class_ids = data.getlist('class_ids') if hasattr(data, 'getlist') else data.get('class_ids')
        else:
            class_ids = None
        if 'section_ids' in data:
            section_ids = data.getlist('section_ids') if hasattr(data, 'getlist') else data.get('section_ids')
        else:
            section_ids = None
        audience = updates.get('audience', ann.audience)

        if audience == 'CLASS':
            if 'audience' in data and class_ids is None:
                raise ValidationException('class_ids are required for CLASS audience.')
            if class_ids is not None and not class_ids:
                raise ValidationException('class_ids are required for CLASS audience.')
            if class_ids:
                found = self.storage.get_classes_by_ids(class_ids, profile.school_id)
                if len(found) != len(class_ids):
                    raise ValidationException(constants.CLASS_NOT_FOUND)
        elif audience == 'SECTION':
            if 'audience' in data and section_ids is None:
                raise ValidationException('section_ids are required for SECTION audience.')
            if section_ids is not None and not section_ids:
                raise ValidationException('section_ids are required for SECTION audience.')
            if section_ids:
                found = self.storage.get_sections_by_ids(section_ids, profile.school_id)
                if len(found) != len(section_ids):
                    raise ValidationException(constants.SECTION_NOT_FOUND)
        else:
            class_ids = []
            section_ids = []

        ann = self.storage.update_announcement(
            announcement=ann,
            updates=updates,
            class_ids=class_ids,
            section_ids=section_ids,
            files=files,
        )
        return self.presenter.announcement_update_success(announcement=ann)


class DeleteAnnouncementInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def delete_announcement(self, user, announcement_id):
        _ensure_principal(user)
        profile = self.storage.get_principal_profile(user)
        if profile is None:
            raise NotFoundException('Principal profile not found.')

        ann = self.storage.get_announcement(announcement_id=announcement_id, school_id=profile.school_id)
        if ann is None:
            raise NotFoundException('Announcement not found.')

        self.storage.delete_announcement(announcement=ann)
        return self.presenter.announcement_delete_success()
