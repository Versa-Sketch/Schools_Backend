from django.db import IntegrityError
from django.db.models import ProtectedError

from core.exceptions import NotFoundException, ValidationException
from .base import _ensure_principal


class ListClassesInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def list_classes(self, user):
        _ensure_principal(user)
        profile = self.storage.get_principal_profile(user)
        if profile is None:
            raise NotFoundException('Principal profile not found.')

        classes = self.storage.get_classes_for_school(profile.school_id)
        return self.presenter.class_list_success(classes=classes)


class CreateClassInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def create_class(self, user, data):
        _ensure_principal(user)
        profile = self.storage.get_principal_profile(user)
        if profile is None:
            raise NotFoundException('Principal profile not found.')

        name = data.get('name')
        if not name:
            raise ValidationException('name is required.')

        display_order = data.get('display_order', 0)

        try:
            academic_class = self.storage.create_class(
                school=profile.school,
                name=name,
                display_order=display_order,
            )
        except IntegrityError:
            raise ValidationException('A class with this name already exists in your school.')

        return self.presenter.class_created(academic_class=academic_class)


class UpdateClassInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def update_class(self, user, class_id, data):
        _ensure_principal(user)
        profile = self.storage.get_principal_profile(user)
        if profile is None:
            raise NotFoundException('Principal profile not found.')

        academic_class = self.storage.get_academic_class_by_id(profile.school_id, class_id)
        if academic_class is None:
            raise NotFoundException('Class not found.')

        name = data.get('name')
        display_order = data.get('display_order')

        try:
            academic_class = self.storage.update_class(
                academic_class=academic_class,
                name=name,
                display_order=display_order,
            )
        except IntegrityError:
            raise ValidationException('A class with this name already exists in your school.')

        return self.presenter.class_success(academic_class=academic_class)


class DeleteClassInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def delete_class(self, user, class_id):
        _ensure_principal(user)
        profile = self.storage.get_principal_profile(user)
        if profile is None:
            raise NotFoundException('Principal profile not found.')

        academic_class = self.storage.get_academic_class_by_id(profile.school_id, class_id)
        if academic_class is None:
            raise NotFoundException('Class not found.')

        try:
            self.storage.delete_class(academic_class)
        except ProtectedError:
            raise ValidationException('Cannot delete class because it contains sections or students.')

        return self.presenter.class_deleted()
