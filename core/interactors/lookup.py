from core.exceptions import NotFoundException


def _require_school(profile):
    if profile is None:
        raise NotFoundException('No school associated with this user.')
    school = getattr(profile, 'school', None)
    if school is None:
        raise NotFoundException('No school associated with this user.')
    return school


class ClassListInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def get_classes(self, user):
        profile = self.storage.get_user_profile(user)
        school = _require_school(profile)
        classes = self.storage.get_classes_for_school(school_id=school.id)
        return self.presenter.class_list_success(classes=classes)


class SectionListInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def get_sections(self, user, class_id=None):
        profile = self.storage.get_user_profile(user)
        school = _require_school(profile)
        sections = self.storage.get_sections_for_school(school_id=school.id, class_id=class_id)
        return self.presenter.section_list_success(sections=sections)


class SubjectListInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def get_subjects(self, user):
        profile = self.storage.get_user_profile(user)
        school = _require_school(profile)
        subjects = self.storage.get_subjects_for_school(school_id=school.id)
        return self.presenter.subject_list_success(subjects=subjects)
