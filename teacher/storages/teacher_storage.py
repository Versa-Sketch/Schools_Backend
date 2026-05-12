from django.db import transaction
from django.db.models import Prefetch
from django.utils import timezone

from core.models import (
    AbsentNotificationLog,
    AttendanceSession,
    Announcement,
    AnnouncementAttachment,
    AnnouncementTarget,
    Homework,
    ParentQuery,
    ParentQueryReply,
    SchoolConfiguration,
    Section,
    StudentAttendance,
    StudyMaterial,
    Subject,
    ATTENDANCE_STATUS_ABSENT,
    NOTIFICATION_CHANNEL_WHATSAPP,
)
from student.models import StudentProfile


class TeacherDB:
    def get_teacher_profile(self, user):
        return getattr(user, 'teacherprofile', None)

    def get_assigned_sections(self, teacher_profile):
        from django.db.models import Count, Q as DQ
        student_count_annotation = Count('studentprofile', filter=DQ(studentprofile__is_active=True))
        assigned = list(
            teacher_profile.assigned_sections
            .select_related('academic_class')
            .annotate(active_student_count=student_count_annotation)
        )
        class_teacher = list(
            Section.objects.filter(class_teacher=teacher_profile)
            .select_related('academic_class')
            .annotate(active_student_count=student_count_annotation)
        )
        merged = {s.id: s for s in assigned}
        merged.update({s.id: s for s in class_teacher})
        return list(merged.values()), set(s.id for s in class_teacher)

    def get_section_by_id(self, section_id, school_id):
        try:
            return Section.objects.select_related('academic_class').get(id=section_id, school_id=school_id)
        except Section.DoesNotExist:
            return None

    def is_section_accessible(self, teacher_profile, section_id):
        return (
            teacher_profile.assigned_sections.filter(id=section_id).exists() or
            Section.objects.filter(id=section_id, class_teacher=teacher_profile).exists()
        )

    def is_class_teacher(self, teacher_profile, section_id):
        return Section.objects.filter(id=section_id, class_teacher=teacher_profile).exists()

    def get_students_for_section(self, section_id):
        return StudentProfile.objects.filter(section_id=section_id, is_active=True).order_by('name')

    def get_school_configuration(self, school_id):
        try:
            return SchoolConfiguration.objects.get(school_id=school_id)
        except SchoolConfiguration.DoesNotExist:
            return None

    # --- Attendance ---

    def get_or_create_attendance_session(self, teacher_profile, section, date, slot):
        session, _ = AttendanceSession.objects.get_or_create(
            section=section, date=date, slot=slot,
            defaults={'school': section.school, 'taken_by': teacher_profile},
        )
        return session

    def get_attendance_session_by_id(self, session_id, school_id):
        try:
            return AttendanceSession.objects.select_related('section', 'taken_by').get(
                id=session_id, school_id=school_id
            )
        except AttendanceSession.DoesNotExist:
            return None

    def get_attendance_records(self, session_id):
        return StudentAttendance.objects.filter(session_id=session_id).select_related('student')

    def bulk_set_attendance(self, session, records):
        with transaction.atomic():
            StudentAttendance.objects.filter(session=session).delete()
            StudentAttendance.objects.bulk_create([
                StudentAttendance(session=session, student_id=r['student_id'], status=r['status'])
                for r in records
            ])
        return StudentAttendance.objects.filter(session=session).select_related('student')

    def confirm_attendance_session(self, session):
        session.confirmed_at = timezone.now()
        session.save(update_fields=['confirmed_at', 'updated_at'])
        return session

    def create_absent_notification_logs(self, session, school_id):
        from parent.models import ParentProfile
        absent_records = StudentAttendance.objects.filter(
            session=session, status=ATTENDANCE_STATUS_ABSENT
        ).select_related('student')
        count = 0
        for record in absent_records:
            for parent in ParentProfile.objects.filter(students=record.student, school_id=school_id):
                AbsentNotificationLog.objects.create(
                    attendance=record, parent=parent, channel=NOTIFICATION_CHANNEL_WHATSAPP,
                )
                count += 1
        return count

    # --- Announcements ---

    def create_teacher_announcement(self, teacher_profile, section, title, body, files, publish_now):
        with transaction.atomic():
            ann = Announcement.objects.create(
                school=section.school, author=teacher_profile.user, author_role='TEACHER',
                title=title, body=body, audience='SECTION',
                published_at=timezone.now() if publish_now else None, is_active=True,
            )
            AnnouncementTarget.objects.create(announcement=ann, section=section)
            for f in (files or []):
                from core.services.s3_upload import upload_to_s3, ATTACHMENT_TYPES
                url = upload_to_s3(f, 'announcements', allowed_types=ATTACHMENT_TYPES)
                AnnouncementAttachment.objects.create(
                    announcement=ann, file=url, filename=f.name,
                    content_type=getattr(f, 'content_type', ''),
                )
        return Announcement.objects.prefetch_related('announcementattachment_set').get(id=ann.id)

    # --- Study Materials ---

    def get_subject_by_id(self, subject_id, school_id):
        try:
            return Subject.objects.get(id=subject_id, school_id=school_id, is_active=True)
        except Subject.DoesNotExist:
            return None

    def create_study_material(self, teacher_profile, section, subject, title, description, file, material_date):
        from core.services.s3_upload import upload_to_s3, ATTACHMENT_TYPES
        url = upload_to_s3(file, 'study_materials', allowed_types=ATTACHMENT_TYPES)
        return StudyMaterial.objects.create(
            school=section.school, section=section, subject=subject,
            uploaded_by=teacher_profile, title=title, description=description or '',
            file=url, material_date=material_date,
        )

    def get_study_materials(self, teacher_profile, section_id=None, subject_id=None, date_from=None, date_to=None):
        qs = StudyMaterial.objects.filter(uploaded_by=teacher_profile).select_related('subject', 'uploaded_by')
        if section_id:
            qs = qs.filter(section_id=section_id)
        if subject_id:
            qs = qs.filter(subject_id=subject_id)
        if date_from:
            qs = qs.filter(material_date__gte=date_from)
        if date_to:
            qs = qs.filter(material_date__lte=date_to)
        return qs

    # --- Homework ---

    def create_homework(self, teacher_profile, section, subject, description, deadline):
        return Homework.objects.create(
            school=section.school, section=section, subject=subject,
            assigned_by=teacher_profile, description=description, deadline=deadline,
        )

    def get_homework(self, teacher_profile, section_id=None, subject_id=None, deadline_from=None, deadline_to=None):
        qs = Homework.objects.filter(assigned_by=teacher_profile).select_related('subject', 'assigned_by')
        if section_id:
            qs = qs.filter(section_id=section_id)
        if subject_id:
            qs = qs.filter(subject_id=subject_id)
        if deadline_from:
            qs = qs.filter(deadline__gte=deadline_from)
        if deadline_to:
            qs = qs.filter(deadline__lte=deadline_to)
        return qs

    # --- Parent Queries ---

    def get_parent_queries(self, teacher_profile, status=None, section_id=None):
        qs = ParentQuery.objects.filter(assigned_teacher=teacher_profile).select_related('parent', 'student', 'section')
        if status:
            qs = qs.filter(status=status)
        if section_id:
            qs = qs.filter(section_id=section_id)
        return qs

    def get_parent_query_by_id(self, query_id, teacher_profile):
        try:
            return ParentQuery.objects.select_related(
                'parent', 'student', 'section', 'assigned_teacher'
            ).get(id=query_id, assigned_teacher=teacher_profile)
        except ParentQuery.DoesNotExist:
            return None

    def create_query_reply(self, query, sender, message, mark_answered):
        with transaction.atomic():
            reply = ParentQueryReply.objects.create(query=query, sender=sender, message=message)
            if mark_answered and query.status == 'OPEN':
                query.status = 'ANSWERED'
                query.save(update_fields=['status', 'updated_at'])
        return reply, query

    def close_query(self, query):
        query.status = 'CLOSED'
        query.save(update_fields=['status', 'updated_at'])
        return query

    def get_parent_query_with_replies(self, query_id, teacher_profile):
        try:
            return ParentQuery.objects.select_related(
                'parent', 'student', 'section', 'assigned_teacher'
            ).prefetch_related(
                Prefetch('parentqueryreply_set', queryset=ParentQueryReply.objects.select_related('sender'))
            ).get(id=query_id, assigned_teacher=teacher_profile)
        except ParentQuery.DoesNotExist:
            return None
