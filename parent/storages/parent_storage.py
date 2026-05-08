from django.db.models import Q
from django.db import transaction

from core.models import (
    AcademicCalendarEvent,
    Announcement,
    Homework,
    ParentQuery,
    ParentQueryReply,
    SchoolConfiguration,
    StudentAttendance,
    StudyMaterial,
)
from student.models import StudentProfile


class ParentDB:
    def get_parent_profile(self, user):
        profile = getattr(user, 'parentprofile', None)
        if profile is None:
            return None
        from parent.models import ParentProfile
        return ParentProfile.objects.select_related('school', 'user').get(pk=profile.pk)

    def get_linked_students(self, parent_profile):
        return parent_profile.students.select_related(
            'academic_class', 'section', 'school'
        ).filter(is_active=True)

    def is_student_linked(self, parent_profile, student_id):
        return parent_profile.students.filter(id=student_id).exists()

    def get_linked_student_by_id(self, parent_profile, student_id):
        try:
            return parent_profile.students.select_related(
                'academic_class', 'section', 'school'
            ).get(id=student_id)
        except StudentProfile.DoesNotExist:
            return None

    def get_school_configuration(self, school_id):
        try:
            return SchoolConfiguration.objects.get(school_id=school_id)
        except SchoolConfiguration.DoesNotExist:
            return None

    def get_attendance_for_student(self, student_profile, date_from=None, date_to=None, slot=None, status=None):
        qs = StudentAttendance.objects.filter(
            student=student_profile, session__confirmed_at__isnull=False,
        ).select_related('session')
        if date_from:
            qs = qs.filter(session__date__gte=date_from)
        if date_to:
            qs = qs.filter(session__date__lte=date_to)
        if slot:
            qs = qs.filter(session__slot=slot)
        if status:
            qs = qs.filter(status=status)
        return qs.order_by('-session__date')

    def get_announcements_for_student(self, student_profile, audience=None, published_after=None):
        q = (
            Q(audience='SCHOOL') |
            Q(audience='CLASS', announcementtarget__academic_class_id=student_profile.academic_class_id) |
            Q(audience='SECTION', announcementtarget__section_id=student_profile.section_id)
        )
        qs = Announcement.objects.filter(
            school=student_profile.school, is_active=True, published_at__isnull=False,
        ).filter(q).distinct().prefetch_related('announcementattachment_set')
        if audience:
            qs = qs.filter(audience=audience)
        if published_after:
            qs = qs.filter(published_at__gte=published_after)
        return qs

    def get_study_materials_for_student(self, student_profile, subject_id=None, date_from=None, date_to=None):
        qs = StudyMaterial.objects.filter(section=student_profile.section).select_related('subject', 'uploaded_by')
        if subject_id:
            qs = qs.filter(subject_id=subject_id)
        if date_from:
            qs = qs.filter(material_date__gte=date_from)
        if date_to:
            qs = qs.filter(material_date__lte=date_to)
        return qs

    def get_homework_for_student(self, student_profile, subject_id=None, deadline_from=None, deadline_to=None):
        qs = Homework.objects.filter(section=student_profile.section).select_related('subject', 'assigned_by')
        if subject_id:
            qs = qs.filter(subject_id=subject_id)
        if deadline_from:
            qs = qs.filter(deadline__gte=deadline_from)
        if deadline_to:
            qs = qs.filter(deadline__lte=deadline_to)
        return qs

    def get_calendar_events_for_student(self, student_profile, event_type=None, start_date=None, end_date=None):
        qs = AcademicCalendarEvent.objects.filter(
            school=student_profile.school, visible_to__icontains='PARENT',
        )
        if event_type:
            qs = qs.filter(event_type=event_type)
        if start_date:
            qs = qs.filter(end_date__gte=start_date)
        if end_date:
            qs = qs.filter(start_date__lte=end_date)
        return qs

    def create_query(self, parent_profile, student_profile, subject, message):
        section = student_profile.section
        return ParentQuery.objects.create(
            school=student_profile.school,
            parent=parent_profile,
            student=student_profile,
            section=section,
            assigned_teacher=section.class_teacher,
            subject=subject,
            message=message,
        )

    def get_queries_for_parent(self, parent_profile, student_id=None, status=None):
        qs = ParentQuery.objects.filter(parent=parent_profile).select_related('student', 'assigned_teacher', 'section')
        if student_id:
            qs = qs.filter(student_id=student_id)
        if status:
            qs = qs.filter(status=status)
        return qs

    def get_query_by_id(self, query_id, parent_profile):
        try:
            return ParentQuery.objects.prefetch_related(
                'parentqueryreply_set__sender'
            ).select_related('student', 'assigned_teacher', 'section').get(
                id=query_id, parent=parent_profile
            )
        except ParentQuery.DoesNotExist:
            return None

    def add_parent_reply(self, query, sender, message):
        return ParentQueryReply.objects.create(query=query, sender=sender, message=message)
