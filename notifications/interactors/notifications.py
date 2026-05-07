class ListNotificationsInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def list_notifications(self, user, unread_only=False):
        notifications = self.storage.get_notifications_for_user(user, unread_only=unread_only)
        unread_count = self.storage.get_unread_count(user)
        return self.presenter.list_success(notifications=notifications, unread_count=unread_count)


class MarkReadInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def mark_read(self, user, notification_ids=None):
        count = self.storage.mark_as_read(user, notification_ids=notification_ids)
        return self.presenter.mark_read_success(count=count)


class UnreadCountInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def get_count(self, user):
        count = self.storage.get_unread_count(user)
        return self.presenter.unread_count_success(count=count)
