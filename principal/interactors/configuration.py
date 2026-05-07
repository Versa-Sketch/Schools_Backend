from core.exceptions import NotFoundException, ValidationException
from principal import constants
from .base import _ensure_principal


class GetConfigurationInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def get_configuration(self, user):
        _ensure_principal(user)
        profile = self.storage.get_principal_profile(user)
        if profile is None:
            raise NotFoundException(constants.CONFIGURATION_NOT_FOUND)
        config = self.storage.get_school_configuration(school_id=profile.school_id)
        if config is None:
            raise NotFoundException(constants.CONFIGURATION_NOT_FOUND)
        return self.presenter.configuration_success(config=config)


class UpdateConfigurationInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def update_configuration(self, user, data):
        _ensure_principal(user)
        profile = self.storage.get_principal_profile(user)
        if profile is None:
            raise NotFoundException(constants.CONFIGURATION_NOT_FOUND)
        config = self.storage.get_school_configuration(school_id=profile.school_id)
        if config is None:
            raise NotFoundException(constants.CONFIGURATION_NOT_FOUND)

        allowed_fields = {'attendance_frequency', 'whatsapp_absent_automation_enabled', 'parent_query_enabled'}
        updates = {k: v for k, v in data.items() if k in allowed_fields}

        freq = updates.get('attendance_frequency')
        if freq and freq not in ('ONCE', 'TWICE'):
            raise ValidationException('attendance_frequency must be ONCE or TWICE.')

        config = self.storage.update_school_configuration(config, updates)
        return self.presenter.configuration_success(config=config)
