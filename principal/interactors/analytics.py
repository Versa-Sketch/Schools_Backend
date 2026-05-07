from .base import _ensure_principal


class AnalyticsInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def get_analytics(self, user):
        _ensure_principal(user)
        return self.presenter.analytics_success()
