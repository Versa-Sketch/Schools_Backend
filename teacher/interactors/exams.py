from .base import _ensure_teacher


class ExamMarksNotImplementedInteractor:
    def __init__(self, presenter):
        self.presenter = presenter

    def respond(self, user):
        _ensure_teacher(user)
        return self.presenter.exam_not_implemented()
