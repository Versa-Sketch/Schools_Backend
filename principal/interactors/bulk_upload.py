from core.exceptions import NotFoundException, ValidationException
from principal import constants
from .base import _ensure_principal


class BulkUploadStudentsInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def bulk_upload(self, user, csv_file):
        _ensure_principal(user)
        profile = self.storage.get_principal_profile(user)
        if profile is None:
            raise NotFoundException('Principal profile not found.')
        if csv_file is None:
            raise ValidationException('csv_file is required.')

        batch = self.storage.create_bulk_upload_batch(
            school=profile.school, principal_profile=profile, csv_file=csv_file,
        )
        batch = self.storage.process_bulk_upload(batch=batch, school=profile.school)
        from notifications.service import NotificationService
        NotificationService.bulk_upload_complete(batch.id, user.id)
        return self.presenter.bulk_upload_success(batch=batch)


class GetBulkUploadStatusInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def get_status(self, user, batch_id):
        _ensure_principal(user)
        profile = self.storage.get_principal_profile(user)
        if profile is None:
            raise NotFoundException('Principal profile not found.')
        batch = self.storage.get_bulk_upload_batch(batch_id=batch_id, school_id=profile.school_id)
        if batch is None:
            raise NotFoundException(constants.BATCH_NOT_FOUND)
        rows = self.storage.get_student_upload_rows(batch_id=batch_id)
        return self.presenter.bulk_upload_success(batch=batch, rows=rows)
