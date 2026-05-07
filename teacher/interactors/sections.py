from core.exceptions import NotFoundException, PermissionDeniedException
from teacher import constants
from .base import _ensure_teacher


class ListSectionsInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def list_sections(self, user):
        _ensure_teacher(user)
        teacher = self.storage.get_teacher_profile(user)
        if teacher is None:
            raise NotFoundException('Teacher profile not found.')
        sections, class_teacher_ids = self.storage.get_assigned_sections(teacher)
        return self.presenter.section_list_success(sections=sections, class_teacher_section_ids=class_teacher_ids)


class ListSectionStudentsInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def list_students(self, user, section_id):
        _ensure_teacher(user)
        teacher = self.storage.get_teacher_profile(user)
        if teacher is None:
            raise NotFoundException('Teacher profile not found.')
        if not self.storage.is_section_accessible(teacher, section_id):
            raise PermissionDeniedException(constants.SECTION_NOT_ASSIGNED)
        students = self.storage.get_students_for_section(section_id)
        return self.presenter.student_list_success(students=students)
