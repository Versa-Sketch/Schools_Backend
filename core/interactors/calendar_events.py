from core.exceptions import NotFoundException


class CalendarEventListInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def get_calendar_events(self, user, event_type=None, start_date=None, end_date=None):
        profile = self.storage.get_user_profile(user)
        if profile is None:
            raise NotFoundException('No school associated with this user.')
        school = getattr(profile, 'school', None)
        if school is None:
            raise NotFoundException('No school associated with this user.')
        events = self.storage.get_calendar_events_for_role(
            school_id=school.id,
            role=user.role,
            event_type=event_type,
            start_date=start_date,
            end_date=end_date,
        )
        return self.presenter.calendar_list_success(events=events)
