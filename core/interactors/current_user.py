class CurrentUserInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def get_current_user(self, user):
        profile = self.storage.get_user_profile(user)
        return self.presenter.success(user=user, profile=profile)
