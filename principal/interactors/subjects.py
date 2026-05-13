from django.db import IntegrityError
from django.db.models import ProtectedError

from core.exceptions import NotFoundException, ValidationException
from .base import _ensure_principal


class CreateSubjectInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def create_subject(self, user, data):
        _ensure_principal(user)
        profile = self.storage.get_principal_profile(user)
        if profile is None:
            raise NotFoundException('Principal profile not found.')

        name = data.get('name')
        if not name:
            raise ValidationException('name is required.')

        code = data.get('code', '')
        is_active = data.get('is_active', True)

        try:
            subject = self.storage.create_subject(
                school=profile.school,
                name=name,
                code=code,
                is_active=is_active,
            )
        except IntegrityError:
            raise ValidationException('A subject with this name or code already exists in your school.')

        return self.presenter.subject_created(subject=subject)


class UpdateSubjectInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def update_subject(self, user, subject_id, data):
        _ensure_principal(user)
        profile = self.storage.get_principal_profile(user)
        if profile is None:
            raise NotFoundException('Principal profile not found.')

        subject = self.storage.get_admin_subject_by_id(subject_id, profile.school_id)
        if subject is None:
            raise NotFoundException('Subject not found.')

        name = data.get('name')
        code = data.get('code')
        is_active = data.get('is_active')

        try:
            subject = self.storage.update_subject(
                subject=subject,
                name=name,
                code=code,
                is_active=is_active,
            )
        except IntegrityError:
            raise ValidationException('A subject with this name or code already exists in your school.')

        return self.presenter.subject_success(subject=subject)


class DeleteSubjectInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def delete_subject(self, user, subject_id):
        _ensure_principal(user)
        profile = self.storage.get_principal_profile(user)
        if profile is None:
            raise NotFoundException('Principal profile not found.')

        subject = self.storage.get_admin_subject_by_id(subject_id, profile.school_id)
        if subject is None:
            raise NotFoundException('Subject not found.')

        try:
            self.storage.delete_subject(subject)
        except ProtectedError:
            raise ValidationException('Cannot delete subject because it is used in teachers, materials, or homework.')

        return self.presenter.subject_deleted()
