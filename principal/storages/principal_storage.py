import csv
import io

from django.db import transaction
from django.utils import timezone

from core.models import (
    AcademicCalendarEvent,
    AcademicClass,
    Announcement,
    AnnouncementAttachment,
    AnnouncementTarget,
    SchoolConfiguration,
    Section,
    Subject,
    StudentBulkUploadBatch,
    StudentBulkUploadRow,
    User,
    UPLOAD_BATCH_STATUS_PROCESSING,
    UPLOAD_BATCH_STATUS_COMPLETED,
    UPLOAD_ROW_STATUS_SUCCESS,
    UPLOAD_ROW_STATUS_FAILED,
)
from teacher.models import TeacherProfile
from student.models import StudentProfile
from parent.models import ParentProfile


class PrincipalDB:
    def get_principal_profile(self, user):
        if user.role == 'ADMIN':
            return getattr(user, 'adminprofile', None)
        return getattr(user, 'principalprofile', None)

    # --- School Configuration ---

    def get_school_configuration(self, school_id):
        try:
            return SchoolConfiguration.objects.select_related('school').get(school_id=school_id)
        except SchoolConfiguration.DoesNotExist:
            return None

    def update_school_configuration(self, config, updates):
        for key, value in updates.items():
            setattr(config, key, value)
        config.save()
        return config

    # --- Sections ---

    def get_sections_for_principal(self, school_id, class_id=None):
        qs = Section.objects.filter(school_id=school_id).select_related('academic_class', 'class_teacher')
        if class_id:
            qs = qs.filter(academic_class_id=class_id)
        return qs

    def get_section_by_id(self, section_id, school_id):
        try:
            return Section.objects.select_related('academic_class', 'class_teacher').get(
                id=section_id, school_id=school_id
            )
        except Section.DoesNotExist:
            return None

    def update_section_query_setting(self, section, parent_query_enabled):
        section.parent_query_enabled = parent_query_enabled
        section.save(update_fields=['parent_query_enabled', 'updated_at'])
        return section

    # --- Teachers ---

    def get_teachers_for_school(self, school_id, subject_id=None, section_id=None, search=None):
        from django.db.models import Q
        qs = TeacherProfile.objects.filter(school_id=school_id).select_related(
            'user', 'primary_subject'
        ).prefetch_related('assigned_sections__academic_class')
        if subject_id:
            qs = qs.filter(primary_subject_id=subject_id)
        if section_id:
            qs = qs.filter(assigned_sections__id=section_id)
        if search:
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(mobile_number__icontains=search) |
                Q(user__username__icontains=search)
            )
        return qs.distinct()

    def get_teacher_by_id(self, teacher_id, school_id):
        try:
            return TeacherProfile.objects.select_related(
                'user', 'primary_subject'
            ).prefetch_related('assigned_sections__academic_class').get(id=teacher_id, school_id=school_id)
        except TeacherProfile.DoesNotExist:
            return None

    def get_subject_by_id(self, subject_id, school_id):
        try:
            return Subject.objects.get(id=subject_id, school_id=school_id, is_active=True)
        except Subject.DoesNotExist:
            return None

    def get_sections_by_ids(self, section_ids, school_id):
        return list(Section.objects.filter(id__in=section_ids, school_id=school_id))

    def get_classes_by_ids(self, class_ids, school_id):
        return list(AcademicClass.objects.filter(id__in=class_ids, school_id=school_id))

    def username_exists(self, username):
        return User.objects.filter(username=username).exists()

    def create_teacher(self, school, name, mobile_number, username, password, primary_subject=None, sections=None):
        with transaction.atomic():
            user = User.objects.create_user(username=username, password=password, role='TEACHER')
            profile = TeacherProfile.objects.create(
                user=user, school=school, name=name,
                mobile_number=mobile_number, primary_subject=primary_subject,
            )
            if sections:
                profile.assigned_sections.set(sections)
        return TeacherProfile.objects.select_related(
            'user', 'primary_subject'
        ).prefetch_related('assigned_sections__academic_class').get(id=profile.id)

    def update_teacher(self, teacher, updates, sections=None):
        for key, value in updates.items():
            setattr(teacher, key, value)
        teacher.save()
        if sections is not None:
            teacher.assigned_sections.set(sections)
        return TeacherProfile.objects.select_related(
            'user', 'primary_subject'
        ).prefetch_related('assigned_sections__academic_class').get(id=teacher.id)

    # --- Bulk Upload ---

    def create_bulk_upload_batch(self, school, principal_profile, csv_file):
        return StudentBulkUploadBatch.objects.create(
            school=school, uploaded_by=principal_profile.user, csv_file=csv_file,
        )

    def process_bulk_upload(self, batch, school):
        batch.status = UPLOAD_BATCH_STATUS_PROCESSING
        batch.save(update_fields=['status', 'updated_at'])

        csv_file = batch.csv_file
        csv_file.open('r')
        raw = csv_file.read()
        csv_file.close()
        if isinstance(raw, bytes):
            raw = raw.decode('utf-8-sig')

        reader = csv.DictReader(io.StringIO(raw))
        rows = list(reader)
        batch.total_rows = len(rows)
        batch.save(update_fields=['total_rows', 'updated_at'])

        success_count = 0
        error_count = 0
        for i, row in enumerate(rows, start=1):
            row_obj = StudentBulkUploadRow.objects.create(batch=batch, row_number=i, raw_data=dict(row))
            try:
                with transaction.atomic():
                    self._process_upload_row(row, school, row_obj, i)
                row_obj.refresh_from_db()
                success_count += 1
            except Exception as e:
                row_obj.status = UPLOAD_ROW_STATUS_FAILED
                row_obj.error_message = str(e)
                row_obj.save()
                error_count += 1

        batch.success_count = success_count
        batch.error_count = error_count
        batch.status = UPLOAD_BATCH_STATUS_COMPLETED
        batch.save(update_fields=['success_count', 'error_count', 'status', 'updated_at'])
        return batch

    def _process_upload_row(self, row, school, row_obj, index):
        class_name = row.get('class', '').strip()
        section_name = row.get('section', '').strip()
        student_name = row.get('student_name', '').strip()
        parent_name = row.get('parent_name', '').strip()
        parent_mobile = row.get('parent_mobile_number', '').strip()

        if not all([class_name, section_name, student_name, parent_name, parent_mobile]):
            raise ValueError('Missing required fields.')

        academic_class = AcademicClass.objects.get(school=school, name__iexact=class_name)
        section = Section.objects.get(academic_class=academic_class, name__iexact=section_name)

        student_username = row.get('student_username', '').strip() or f"student_{school.id}_{index}"
        if User.objects.filter(username=student_username).exists():
            student_username = f"{student_username}_{index}"

        student_user = User.objects.create_user(
            username=student_username, password=f"pass@{parent_mobile}", role='STUDENT',
        )
        student_profile = StudentProfile.objects.create(
            user=student_user, school=school, name=student_name,
            academic_class=academic_class, section=section,
            roll_number=row.get('roll_number', '').strip(),
            admission_number=row.get('admission_number', '').strip(),
        )

        parent_profile = ParentProfile.objects.filter(school=school, mobile_number=parent_mobile).first()
        if parent_profile is None:
            parent_username = row.get('parent_username', '').strip() or f"parent_{school.id}_{parent_mobile}"
            if User.objects.filter(username=parent_username).exists():
                parent_username = f"{parent_username}_{index}"
            parent_user = User.objects.create_user(
                username=parent_username, password=f"pass@{parent_mobile}", role='PARENT',
            )
            parent_profile = ParentProfile.objects.create(
                user=parent_user, school=school, name=parent_name, mobile_number=parent_mobile,
            )
        parent_profile.students.add(student_profile)

        row_obj.status = UPLOAD_ROW_STATUS_SUCCESS
        row_obj.created_student = student_profile
        row_obj.created_parent = parent_profile
        row_obj.save()

    def get_bulk_upload_batch(self, batch_id, school_id):
        try:
            return StudentBulkUploadBatch.objects.get(id=batch_id, school_id=school_id)
        except StudentBulkUploadBatch.DoesNotExist:
            return None

    # --- Announcements ---

    def create_announcement(self, school, author, title, body, audience, class_ids, section_ids, files, publish_now):
        with transaction.atomic():
            ann = Announcement.objects.create(
                school=school, author=author, author_role='PRINCIPAL',
                title=title, body=body, audience=audience,
                published_at=timezone.now() if publish_now else None, is_active=True,
            )
            if audience == 'CLASS' and class_ids:
                for cid in class_ids:
                    AnnouncementTarget.objects.create(announcement=ann, academic_class_id=cid)
            elif audience == 'SECTION' and section_ids:
                for sid in section_ids:
                    AnnouncementTarget.objects.create(announcement=ann, section_id=sid)
            for f in (files or []):
                from core.services.s3_upload import upload_to_s3, ATTACHMENT_TYPES
                url = upload_to_s3(f, 'announcements', allowed_types=ATTACHMENT_TYPES)
                AnnouncementAttachment.objects.create(
                    announcement=ann, file=url, filename=f.name,
                    content_type=getattr(f, 'content_type', ''),
                )
        return Announcement.objects.prefetch_related('announcementattachment_set').get(id=ann.id)

    # --- Calendar ---

    def create_calendar_event(self, school, title, event_type, start_date, end_date, description, visible_to):
        return AcademicCalendarEvent.objects.create(
            school=school, title=title, event_type=event_type,
            start_date=start_date, end_date=end_date,
            description=description or '', visible_to=visible_to,
        )
