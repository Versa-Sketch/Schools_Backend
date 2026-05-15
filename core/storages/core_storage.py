from django.db.models import Q

from core.models import (
    AcademicCalendarEvent,
    Announcement,
    AcademicClass,
    Section,
    StudentAttendance,
    Subject,
)
from student.models import StudentProfile


class CoreDB:
    def get_user_profile(self, user):
        attr_map = {
            'ADMIN': 'adminprofile',
            'PRINCIPAL': 'principalprofile',
            'TEACHER': 'teacherprofile',
            'STUDENT': 'studentprofile',
            'PARENT': 'parentprofile',
        }
        attr = attr_map.get(user.role)
        if not attr:
            return None
        return getattr(user, attr, None)

    def get_school_configuration(self, school_id):
        from core.models import SchoolConfiguration
        try:
            return SchoolConfiguration.objects.get(school_id=school_id)
        except SchoolConfiguration.DoesNotExist:
            return None

    def get_classes_for_school(self, school_id):
        return AcademicClass.objects.filter(school_id=school_id)

    def get_classes_for_user(self, user, profile, school_id):
        if user.role in ('ADMIN', 'PRINCIPAL'):
            return self.get_classes_for_school(school_id)
        if user.role == 'TEACHER':
            class_ids = profile.assigned_sections.values_list('academic_class_id', flat=True)
            ct_class_ids = Section.objects.filter(school_id=school_id, class_teacher=profile).values_list('academic_class_id', flat=True)
            return AcademicClass.objects.filter(school_id=school_id).filter(
                Q(id__in=class_ids) | Q(id__in=ct_class_ids)
            ).distinct()
        if user.role == 'PARENT':
            class_ids = profile.students.filter(is_active=True).values_list('academic_class_id', flat=True)
            return AcademicClass.objects.filter(school_id=school_id, id__in=class_ids)
        if user.role == 'STUDENT':
            return AcademicClass.objects.filter(school_id=school_id, id=profile.academic_class_id)
        return AcademicClass.objects.none()

    def get_sections_for_school(self, school_id, class_id=None):
        qs = Section.objects.filter(school_id=school_id).select_related(
            'academic_class', 'class_teacher'
        )
        if class_id:
            qs = qs.filter(academic_class_id=class_id)
        return qs

    def get_sections_for_user(self, user, profile, school_id, class_id=None):
        if user.role in ('ADMIN', 'PRINCIPAL'):
            return self.get_sections_for_school(school_id, class_id=class_id)

        qs = Section.objects.filter(school_id=school_id).select_related(
            'academic_class', 'class_teacher'
        )
        if user.role == 'TEACHER':
            class_ids = profile.assigned_sections.values_list('academic_class_id', flat=True)
            qs = qs.filter(Q(academic_class_id__in=class_ids) | Q(class_teacher_id=profile.id))
        elif user.role == 'PARENT':
            section_ids = profile.students.filter(is_active=True).values_list('section_id', flat=True)
            qs = qs.filter(id__in=section_ids)
        elif user.role == 'STUDENT':
            qs = qs.filter(id=profile.section_id)
        else:
            qs = qs.none()
        if class_id:
            qs = qs.filter(academic_class_id=class_id)
        return qs

    def can_access_section(self, user, profile, section_id, school_id):
        if user.role in ('ADMIN', 'PRINCIPAL'):
            return Section.objects.filter(id=section_id, school_id=school_id).exists()
        if user.role == 'TEACHER':
            section = Section.objects.filter(id=section_id, school_id=school_id).first()
            if section is None:
                return False
            return (
                section.class_teacher_id == profile.id or
                profile.assigned_sections.filter(academic_class_id=section.academic_class_id).exists()
            )
        if user.role == 'PARENT':
            return profile.students.filter(section_id=section_id, school_id=school_id, is_active=True).exists()
        if user.role == 'STUDENT':
            return str(profile.section_id) == str(section_id)
        return False

    def get_students_for_section_user(self, user, profile, section_id, school_id):
        qs = StudentProfile.objects.filter(
            section_id=section_id,
            school_id=school_id,
            is_active=True,
        ).select_related('academic_class', 'section', 'school')
        if user.role == 'PARENT':
            qs = qs.filter(id__in=profile.students.values_list('id', flat=True))
        elif user.role == 'STUDENT':
            qs = qs.filter(id=profile.id)
        return qs.order_by('name')

    def get_student_by_id(self, student_id, school_id):
        try:
            return StudentProfile.objects.select_related(
                'academic_class', 'section', 'school'
            ).get(id=student_id, school_id=school_id, is_active=True)
        except StudentProfile.DoesNotExist:
            return None

    def can_access_student(self, user, profile, student, school_id):
        if user.role in ('ADMIN', 'PRINCIPAL'):
            return student.school_id == school_id
        if user.role == 'TEACHER':
            return (
                student.section.class_teacher_id == profile.id or
                profile.assigned_sections.filter(academic_class_id=student.academic_class_id).exists()
            )
        if user.role == 'PARENT':
            return profile.students.filter(id=student.id, is_active=True).exists()
        if user.role == 'STUDENT':
            return profile.id == student.id
        return False

    def get_student_attendance_for_date(self, student, date):
        return list(
            StudentAttendance.objects
            .filter(
                student=student,
                session__date=date,
                session__confirmed_at__isnull=False,
            )
            .select_related('session')
            .order_by('session__slot')
        )

    def get_subjects_for_school(self, school_id):
        return Subject.objects.filter(school_id=school_id, is_active=True)

    def get_calendar_events_for_role(self, school_id, role, event_type=None, start_date=None, end_date=None):
        qs = AcademicCalendarEvent.objects.filter(school_id=school_id)
        if role not in ('ADMIN', 'PRINCIPAL'):
            qs = qs.filter(visible_to__icontains=role)
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

        if user_role not in ('ADMIN', 'PRINCIPAL'):
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
