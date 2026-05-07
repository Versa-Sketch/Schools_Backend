from core.exceptions import NotFoundException, PermissionDeniedException


def _require_school(profile):
    if profile is None:
        raise NotFoundException('No school associated with this user.')
    school = getattr(profile, 'school', None)
    if school is None:
        raise NotFoundException('No school associated with this user.')
    return school


def _get_class_section_ids(user, profile):
    role = user.role
    class_ids = []
    section_ids = []

    if role == 'STUDENT':
        if getattr(profile, 'academic_class_id', None):
            class_ids = [profile.academic_class_id]
        if getattr(profile, 'section_id', None):
            section_ids = [profile.section_id]

    elif role == 'TEACHER':
        assigned = list(profile.assigned_sections.values_list('id', flat=True))
        class_teacher = list(profile.section_set.values_list('id', flat=True))
        section_ids = list(set(assigned + class_teacher))
        if section_ids:
            from core.models import Section
            class_ids = list(set(
                Section.objects.filter(id__in=section_ids).values_list('academic_class_id', flat=True)
            ))

    elif role == 'PARENT':
        students = profile.students.all()
        class_ids = list(set(s.academic_class_id for s in students))
        section_ids = list(set(s.section_id for s in students))

    return class_ids, section_ids


class AnnouncementListInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def get_announcements(self, user, audience=None, published_after=None):
        profile = self.storage.get_user_profile(user)
        school = _require_school(profile)
        class_ids, section_ids = _get_class_section_ids(user, profile)
        announcements = self.storage.get_announcements_visible_to_user(
            school_id=school.id,
            user_role=user.role,
            class_ids=class_ids,
            section_ids=section_ids,
            audience=audience,
            published_after=published_after,
        )
        return self.presenter.announcement_list_success(announcements=announcements)


class AnnouncementDetailInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def get_announcement(self, user, announcement_id):
        profile = self.storage.get_user_profile(user)
        school = _require_school(profile)
        announcement = self.storage.get_announcement_by_id(
            announcement_id=announcement_id,
            school_id=school.id,
        )
        if announcement is None:
            raise NotFoundException('Announcement not found.')

        if user.role != 'PRINCIPAL':
            class_ids, section_ids = _get_class_section_ids(user, profile)
            aud = announcement.audience
            if aud == 'CLASS':
                target_class_ids = [t.academic_class_id for t in announcement.announcementtarget_set.all()]
                if not any(c in target_class_ids for c in class_ids):
                    raise PermissionDeniedException('This announcement is not visible to you.')
            elif aud == 'SECTION':
                target_section_ids = [t.section_id for t in announcement.announcementtarget_set.all()]
                if not any(s in target_section_ids for s in section_ids):
                    raise PermissionDeniedException('This announcement is not visible to you.')

        return self.presenter.announcement_detail_success(announcement=announcement)
