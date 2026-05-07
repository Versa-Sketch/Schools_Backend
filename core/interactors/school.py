from core.exceptions import NotFoundException


class SchoolInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def get_school(self, user):
        profile = self.storage.get_user_profile(user)
        if profile is None:
            raise NotFoundException('No school associated with this user.')
        school = getattr(profile, 'school', None)
        if school is None:
            raise NotFoundException('No school associated with this user.')
        return self.presenter.success(school=school)
