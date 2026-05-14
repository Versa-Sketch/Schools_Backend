from core.exceptions import ValidationException, NotFoundException
from core.services.s3_upload import upload_to_s3, IMAGE_TYPES

def _get_school_id(user, storage):
    if user.role == 'ADMIN':
        profile = getattr(user, 'adminprofile', None)
    elif user.role == 'PRINCIPAL':
        profile = getattr(user, 'principalprofile', None)
    else:
        profile = None

    if profile is None:
        raise NotFoundException("User profile not found.")
    return profile.school_id

class UploadSchoolLogoInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def upload_logo(self, user, logo_file):
        if not logo_file:
            raise ValidationException("Logo file is required.")

        school_id = _get_school_id(user, self.storage)

        logo_url = upload_to_s3(
            file_obj=logo_file,
            folder='schools/logos',
            allowed_types=IMAGE_TYPES
        )

        school = self.storage.update_school_logo(school_id=school_id, logo_url=logo_url)
        if not school:
            raise NotFoundException("School not found.")

        return self.presenter.success(logo_url=school.logo)


class DeleteSchoolLogoInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def delete_logo(self, user):
        school_id = _get_school_id(user, self.storage)

        school = self.storage.update_school_logo(school_id=school_id, logo_url=None)
        if not school:
            raise NotFoundException("School not found.")

        return self.presenter.success(logo_url=None)
