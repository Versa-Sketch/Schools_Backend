from .base import _ensure_parent


class ParentStudentResultsInteractor:
    def __init__(self, presenter):
        self.presenter = presenter

    def respond(self, user):
        _ensure_parent(user)
        return self.presenter.exam_not_implemented()
