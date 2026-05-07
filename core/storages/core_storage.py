from django.db.models import Q

from core.models import (
    AcademicCalendarEvent,
    Announcement,
    AcademicClass,
    Section,
    Subject,
)


class CoreDB:
    def get_user_profile(self, user):
        attr_map = {
            'PRINCIPAL': 'principalprofile',
            'TEACHER': 'teacherprofile',
            'STUDENT': 'studentprofile',
            'PARENT': 'parentprofile',
        }
        attr = attr_map.get(user.role)
        if not attr:
            return None
        return getattr(user, attr, None)

    def get_classes_for_school(self, school_id):
        return AcademicClass.objects.filter(school_id=school_id)

    def get_sections_for_school(self, school_id, class_id=None):
        qs = Section.objects.filter(school_id=school_id).select_related(
            'academic_class', 'class_teacher'
        )
        if class_id:
            qs = qs.filter(academic_class_id=class_id)
        return qs

    def get_subjects_for_school(self, school_id):
        return Subject.objects.filter(school_id=school_id, is_active=True)

    def get_calendar_events_for_role(self, school_id, role, event_type=None, start_date=None, end_date=None):
        qs = AcademicCalendarEvent.objects.filter(school_id=school_id)
        if role != 'PRINCIPAL':
            qs = qs.filter(visible_to__contains=[role])
        if event_type:
            qs = qs.filter(event_type=event_type)
        if start_date:
            qs = qs.filter(end_date__gte=start_date)
        if end_date:
            qs = qs.filter(start_date__lte=end_date)
        return qs

    def get_announcements_visible_to_user(
        self, school_id, user_role, class_ids=None, section_ids=None,
        audience=None, published_after=None,
    ):
        qs = Announcement.objects.filter(
            school_id=school_id,
            is_active=True,
            published_at__isnull=False,
        ).prefetch_related('announcementattachment_set')

        if user_role != 'PRINCIPAL':
            q = Q(audience='SCHOOL')
            if class_ids:
                q |= Q(audience='CLASS', announcementtarget__academic_class_id__in=class_ids)
            if section_ids:
                q |= Q(audience='SECTION', announcementtarget__section_id__in=section_ids)
            qs = qs.filter(q).distinct()

        if audience:
            qs = qs.filter(audience=audience)
        if published_after:
            qs = qs.filter(published_at__gte=published_after)
        return qs

    def get_announcement_by_id(self, announcement_id, school_id):
        try:
            return Announcement.objects.prefetch_related(
                'announcementattachment_set',
                'announcementtarget_set__academic_class',
                'announcementtarget_set__section',
            ).get(id=announcement_id, school_id=school_id, is_active=True)
        except Announcement.DoesNotExist:
            return None
