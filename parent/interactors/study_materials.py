from core.exceptions import NotFoundException
from .base import _ensure_parent, _get_linked_student


class ParentStudentMaterialsInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def get_materials(self, user, student_id, subject_id=None, date_from=None, date_to=None):
        _ensure_parent(user)
        profile = self.storage.get_parent_profile(user)
        if profile is None:
            raise NotFoundException('Parent profile not found.')
        student = _get_linked_student(self.storage, profile, student_id)
        materials = self.storage.get_study_materials_for_student(student, subject_id, date_from, date_to)
        return self.presenter.study_material_list_success(materials=materials)
