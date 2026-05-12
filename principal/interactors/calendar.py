from core.exceptions import NotFoundException, ValidationException
from principal import constants
from .base import _ensure_principal


class CreateCalendarEventInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def create_event(self, user, data):
        _ensure_principal(user)
        profile = self.storage.get_principal_profile(user)
        if profile is None:
            raise NotFoundException('Principal profile not found.')
        school = profile.school

        title = data.get('title', '').strip()
        event_type = data.get('event_type', '').strip()
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        description = data.get('description', '')
        visible_to = data.get('visible_to', [])

        if not title:
            raise ValidationException('title is required.')
        if event_type not in ('HOLIDAY', 'EXAM', 'EVENT'):
            raise ValidationException('event_type must be HOLIDAY, EXAM, or EVENT.')
        if not start_date or not end_date:
            raise ValidationException('start_date and end_date are required.')
        if end_date < start_date:
            raise ValidationException(constants.INVALID_DATE_RANGE)

        valid_roles = {'TEACHER', 'STUDENT', 'PARENT'}
        visible_to = [r for r in visible_to if r in valid_roles]

        event = self.storage.create_calendar_event(
            school=school, title=title, event_type=event_type,
            start_date=start_date, end_date=end_date,
            description=description, visible_to=visible_to,
        )
        from notifications.service import NotificationService
        NotificationService.calendar_event_created(event.id)
        return self.presenter.calendar_event_success(event=event)


class UpdateCalendarEventInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def update_event(self, user, event_id, data):
        _ensure_principal(user)
        profile = self.storage.get_principal_profile(user)
        if profile is None:
            raise NotFoundException('Principal profile not found.')

        event = self.storage.get_calendar_event(event_id=event_id, school_id=profile.school_id)
        if event is None:
            raise NotFoundException('Calendar event not found.')

        updates = {}
        if 'title' in data:
            updates['title'] = data['title'].strip()
        if 'event_type' in data:
            if data['event_type'] not in ('HOLIDAY', 'EXAM', 'EVENT'):
                raise ValidationException('event_type must be HOLIDAY, EXAM, or EVENT.')
            updates['event_type'] = data['event_type']
        if 'start_date' in data:
            updates['start_date'] = data['start_date']
        if 'end_date' in data:
            updates['end_date'] = data['end_date']
        if 'description' in data:
            updates['description'] = data['description']
        if 'visible_to' in data:
            valid_roles = {'TEACHER', 'STUDENT', 'PARENT'}
            updates['visible_to'] = [r for r in data['visible_to'] if r in valid_roles]

        start = updates.get('start_date', event.start_date)
        end = updates.get('end_date', event.end_date)
        if end < start:
            raise ValidationException(constants.INVALID_DATE_RANGE)

        event = self.storage.update_calendar_event(event=event, updates=updates)
        return self.presenter.calendar_event_update_success(event=event)


class DeleteCalendarEventInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def delete_event(self, user, event_id):
        _ensure_principal(user)
        profile = self.storage.get_principal_profile(user)
        if profile is None:
            raise NotFoundException('Principal profile not found.')

        event = self.storage.get_calendar_event(event_id=event_id, school_id=profile.school_id)
        if event is None:
            raise NotFoundException('Calendar event not found.')

        self.storage.delete_calendar_event(event=event)
        return self.presenter.calendar_event_delete_success()
