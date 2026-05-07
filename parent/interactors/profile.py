from core.exceptions import NotFoundException
from .base import _ensure_parent


class ParentProfileInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def get_profile(self, user):
        _ensure_parent(user)
        profile = self.storage.get_parent_profile(user)
        if profile is None:
            raise NotFoundException('Parent profile not found.')
        students = self.storage.get_linked_students(profile)
        school_config = self.storage.get_school_configuration(profile.school_id)
        return self.presenter.profile_success(profile=profile, students=students, school_config=school_config)


class ListLinkedStudentsInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def list_students(self, user):
        _ensure_parent(user)
        profile = self.storage.get_parent_profile(user)
        if profile is None:
            raise NotFoundException('Parent profile not found.')
        students = self.storage.get_linked_students(profile)
        return self.presenter.student_list_success(students=students)
