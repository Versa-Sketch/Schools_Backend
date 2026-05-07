from core.exceptions import NotFoundException
from .base import _ensure_student


class StudentStudyMaterialsInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def get_materials(self, user, subject_id=None, date_from=None, date_to=None):
        _ensure_student(user)
        profile = self.storage.get_student_profile(user)
        if profile is None:
            raise NotFoundException('Student profile not found.')
        materials = self.storage.get_study_materials_for_student(profile, subject_id, date_from, date_to)
        return self.presenter.study_material_list_success(materials=materials)
