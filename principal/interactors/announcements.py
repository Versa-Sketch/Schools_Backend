from core.exceptions import NotFoundException, ValidationException
from principal import constants
from .base import _ensure_principal


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
