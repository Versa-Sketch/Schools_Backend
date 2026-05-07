from core.exceptions import NotFoundException, PermissionDeniedException, ValidationException
from teacher import constants
from .base import _ensure_teacher


class CreateStudyMaterialInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def create_material(self, user, data, file):
        _ensure_teacher(user)
        teacher = self.storage.get_teacher_profile(user)
        if teacher is None:
            raise NotFoundException('Teacher profile not found.')

        section_id = data.get('section_id')
        subject_id = data.get('subject_id')
        title = data.get('title', '').strip()
        description = data.get('description', '')
        material_date = data.get('material_date')

        if not all([section_id, subject_id, title, material_date, file]):
            raise ValidationException('section_id, subject_id, title, material_date, and file are required.')
        if not self.storage.is_section_accessible(teacher, section_id):
            raise PermissionDeniedException(constants.SECTION_NOT_ASSIGNED)

        section = self.storage.get_section_by_id(section_id, teacher.school_id)
        if section is None:
            raise NotFoundException('Section not found.')
        subject = self.storage.get_subject_by_id(subject_id, teacher.school_id)
        if subject is None:
            raise ValidationException(constants.SUBJECT_NOT_ASSIGNED)

        material = self.storage.create_study_material(teacher, section, subject, title, description, file, material_date)
        from notifications.service import NotificationService
        NotificationService.study_material_uploaded(material.id)
        return self.presenter.study_material_success(material=material)


class ListStudyMaterialsInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def list_materials(self, user, section_id=None, subject_id=None, date_from=None, date_to=None):
        _ensure_teacher(user)
        teacher = self.storage.get_teacher_profile(user)
        if teacher is None:
            raise NotFoundException('Teacher profile not found.')
        materials = self.storage.get_study_materials(teacher, section_id, subject_id, date_from, date_to)
        return self.presenter.study_material_list_success(materials=materials)
