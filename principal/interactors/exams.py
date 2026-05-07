from .base import _ensure_principal


class ExamNotImplementedInteractor:
    def __init__(self, presenter):
        self.presenter = presenter

    def respond(self, user):
        _ensure_principal(user)
        return self.presenter.exam_not_implemented()
