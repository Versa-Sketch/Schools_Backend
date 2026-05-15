from core.exceptions import ValidationException
from core.services.s3_upload import upload_to_s3, PROFILE_PIC_TYPES
from core.storages.user_storage import UserDB
from .base import _ensure_principal


class UpdatePrincipalProfilePicInteractor:
    def __init__(self, presenter):
        self.presenter = presenter

    def update(self, user, file):
        _ensure_principal(user)
        if file is None:
            raise ValidationException('profile_pic file is required.')
        url = upload_to_s3(file, 'profile_pics', allowed_types=PROFILE_PIC_TYPES)
        UserDB().update_user_profile_pic(user, url)
        return self.presenter.profile_pic_success(url=url)
