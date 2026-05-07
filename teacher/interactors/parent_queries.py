from core.exceptions import NotFoundException, ValidationException
from teacher import constants
from .base import _ensure_teacher


class ListParentQueriesInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def list_queries(self, user, status=None, section_id=None):
        _ensure_teacher(user)
        teacher = self.storage.get_teacher_profile(user)
        if teacher is None:
            raise NotFoundException('Teacher profile not found.')
        queries = self.storage.get_parent_queries(teacher, status=status, section_id=section_id)
        return self.presenter.query_list_success(queries=queries)


class ReplyToQueryInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def reply(self, user, query_id, data):
        _ensure_teacher(user)
        teacher = self.storage.get_teacher_profile(user)
        if teacher is None:
            raise NotFoundException('Teacher profile not found.')

        query = self.storage.get_parent_query_by_id(query_id, teacher)
        if query is None:
            raise NotFoundException(constants.QUERY_NOT_FOUND)
        if query.status == 'CLOSED':
            raise ValidationException(constants.QUERY_CLOSED)

        message = data.get('message', '').strip()
        mark_answered = data.get('mark_answered', False)
        if not message:
            raise ValidationException('message is required.')

        reply, query = self.storage.create_query_reply(query, user, message, mark_answered)
        from notifications.service import NotificationService
        NotificationService.query_reply_added(reply.id)
        return self.presenter.reply_success(reply=reply, query=query)
