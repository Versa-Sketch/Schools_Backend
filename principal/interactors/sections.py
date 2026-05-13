from django.db import IntegrityError
from django.db.models import ProtectedError

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


class CreateSectionInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def create_section(self, user, data):
        _ensure_principal(user)
        profile = self.storage.get_principal_profile(user)
        if profile is None:
            raise NotFoundException('Principal profile not found.')

        class_id = data.get('class_id')
        name = data.get('name')
        if not class_id or not name:
            raise ValidationException('class_id and name are required.')

        academic_class = self.storage.get_classes_by_ids([class_id], profile.school_id)
        if not academic_class:
            raise ValidationException('Class not found.')
        academic_class = academic_class[0]

        class_teacher_id = data.get('class_teacher_id')
        class_teacher = None
        if class_teacher_id:
            class_teacher = self.storage.get_teacher_by_id(class_teacher_id, profile.school_id)
            if not class_teacher:
                raise ValidationException('Class teacher not found.')

        parent_query_enabled = data.get('parent_query_enabled', True)

        try:
            section = self.storage.create_section(
                school=profile.school,
                academic_class=academic_class,
                name=name,
                class_teacher=class_teacher,
                parent_query_enabled=parent_query_enabled,
            )
        except IntegrityError:
            raise ValidationException('A section with this name already exists in this class.')

        return self.presenter.section_created(section=section)


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

        name = data.get('name')
        parent_query_enabled = data.get('parent_query_enabled')
        class_teacher_id = data.get('class_teacher_id')

        class_teacher = None
        clear_class_teacher = False

        if 'class_teacher_id' in data:
            if class_teacher_id is None:
                clear_class_teacher = True
            else:
                class_teacher = self.storage.get_teacher_by_id(class_teacher_id, profile.school_id)
                if not class_teacher:
                    raise ValidationException('Class teacher not found.')

        try:
            section = self.storage.update_section(
                section=section,
                name=name,
                class_teacher=class_teacher,
                parent_query_enabled=parent_query_enabled,
                clear_class_teacher=clear_class_teacher,
            )
        except IntegrityError:
            raise ValidationException('A section with this name already exists in this class.')

        return self.presenter.section_detail_success(section=section)


class DeleteSectionInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def delete_section(self, user, section_id):
        _ensure_principal(user)
        profile = self.storage.get_principal_profile(user)
        if profile is None:
            raise NotFoundException('Principal profile not found.')

        section = self.storage.get_section_by_id(section_id, profile.school_id)
        if section is None:
            raise NotFoundException('Section not found.')

        try:
            self.storage.delete_section(section)
        except ProtectedError:
            raise ValidationException('Cannot delete section because it contains students or attendance records.')

        return self.presenter.section_deleted()
