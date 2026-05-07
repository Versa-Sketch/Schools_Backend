from core.exceptions import NotFoundException, ValidationException
from .base import _ensure_principal


class ListSectionsInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def list_sections(self, user, class_id=None):
        _ensure_principal(user)
        profile = self.storage.get_principal_profile(user)
        if profile is None:
            raise NotFoundException('Principal profile not found.')
        sections = self.storage.get_sections_for_principal(
            school_id=profile.school_id, class_id=class_id
        )
        return self.presenter.section_list_success(sections=sections)


class UpdateSectionInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def update_section(self, user, section_id, data):
        _ensure_principal(user)
        profile = self.storage.get_principal_profile(user)
        if profile is None:
            raise NotFoundException('Principal profile not found.')

        section = self.storage.get_section_by_id(section_id, profile.school_id)
        if section is None:
            raise NotFoundException('Section not found.')

        if 'parent_query_enabled' not in data:
            raise ValidationException('parent_query_enabled is required.')
        value = data.get('parent_query_enabled')
        if not isinstance(value, bool):
            raise ValidationException('parent_query_enabled must be a boolean.')

        section = self.storage.update_section_query_setting(section, value)
        return self.presenter.section_detail_success(section=section)
