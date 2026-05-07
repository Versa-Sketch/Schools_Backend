from .base import _ensure_student


class StudentExamNotImplementedInteractor:
    def __init__(self, presenter):
        self.presenter = presenter

    def respond(self, user):
        _ensure_student(user)
        return self.presenter.exam_not_implemented()
