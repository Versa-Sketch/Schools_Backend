from core.exceptions import NotFoundException, PermissionDeniedException, ValidationException
from parent import constants
from .base import _ensure_parent, _get_linked_student


class CreateParentQueryInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def create_query(self, user, data):
        _ensure_parent(user)
        profile = self.storage.get_parent_profile(user)
        if profile is None:
            raise NotFoundException('Parent profile not found.')

        student_id = data.get('student_id')
        subject = data.get('subject', '').strip()
        message = data.get('message', '').strip()

        if not all([student_id, subject, message]):
            raise ValidationException('student_id, subject, and message are required.')

        student = _get_linked_student(self.storage, profile, student_id)

        config = self.storage.get_school_configuration(student.school_id)
        if config and not config.parent_query_enabled:
            raise PermissionDeniedException(constants.PARENT_QUERIES_DISABLED)
        if not student.section.parent_query_enabled:
            raise PermissionDeniedException(constants.SECTION_QUERIES_DISABLED)
        if not student.section.class_teacher_id:
            raise ValidationException(constants.SECTION_HAS_NO_CLASS_TEACHER)

        query = self.storage.create_query(profile, student, subject, message)
        from notifications.service import NotificationService
        NotificationService.parent_query_created(query.id)
        return self.presenter.query_detail_success(query=query)


class ListParentQueriesInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def list_queries(self, user, student_id=None, status=None):
        _ensure_parent(user)
        profile = self.storage.get_parent_profile(user)
        if profile is None:
            raise NotFoundException('Parent profile not found.')
        queries = self.storage.get_queries_for_parent(profile, student_id=student_id, status=status)
        return self.presenter.query_list_success(queries=queries)


class GetParentQueryDetailInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def get_query(self, user, query_id):
        _ensure_parent(user)
        profile = self.storage.get_parent_profile(user)
        if profile is None:
            raise NotFoundException('Parent profile not found.')
        query = self.storage.get_query_by_id(query_id, profile)
        if query is None:
            raise NotFoundException(constants.QUERY_NOT_FOUND)
        return self.presenter.query_with_replies_success(query=query)


class AddParentQueryReplyInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def add_reply(self, user, query_id, data):
        _ensure_parent(user)
        profile = self.storage.get_parent_profile(user)
        if profile is None:
            raise NotFoundException('Parent profile not found.')

        query = self.storage.get_query_by_id(query_id, profile)
        if query is None:
            raise NotFoundException(constants.QUERY_NOT_FOUND)
        if query.status == 'CLOSED':
            raise ValidationException(constants.QUERY_CLOSED)

        message = data.get('message', '').strip()
        if not message:
            raise ValidationException('message is required.')

        config = self.storage.get_school_configuration(query.school_id)
        if config and not config.parent_query_enabled:
            raise PermissionDeniedException(constants.PARENT_QUERIES_DISABLED)

        reply = self.storage.add_parent_reply(query, user, message)
        from notifications.service import NotificationService
        NotificationService.query_reply_added(reply.id)
        return self.presenter.reply_success(reply=reply)
