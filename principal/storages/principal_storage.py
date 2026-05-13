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
    AttendanceSession,
    SchoolConfiguration,
    Section,
    StudentAttendance,
    Subject,
    StudentBulkUploadBatch,
    StudentBulkUploadRow,
    TeacherBulkUploadBatch,
    TeacherBulkUploadRow,
    User,
    ATTENDANCE_STATUS_PRESENT,
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
                Q(user__phone_number__icontains=search) |
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

    def create_teacher(self, school, name, phone_number, username, password, primary_subject=None, sections=None):
        with transaction.atomic():
            user = User.objects.create_user(username=username, password=password, role='TEACHER')
            user.phone_number = phone_number
            user.save(update_fields=['phone_number'])
            profile = TeacherProfile.objects.create(
                user=user, school=school, name=name,
                primary_subject=primary_subject,
            )
            if sections:
                profile.assigned_sections.set(sections)
        return TeacherProfile.objects.select_related(
            'user', 'primary_subject'
        ).prefetch_related('assigned_sections__academic_class').get(id=profile.id)

    def update_teacher(self, teacher, updates, sections=None):
        user_fields = {'phone_number'}
        user_updates = {k: v for k, v in updates.items() if k in user_fields}
        profile_updates = {k: v for k, v in updates.items() if k not in user_fields}
        for key, value in profile_updates.items():
            setattr(teacher, key, value)
        teacher.save()
        if user_updates:
            for key, value in user_updates.items():
                setattr(teacher.user, key, value)
            teacher.user.save(update_fields=list(user_updates.keys()))
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
        parent_phone = row.get('parent_phone_number', '').strip()

        if not all([class_name, section_name, student_name, parent_name, parent_phone]):
            raise ValueError('Missing required fields.')

        academic_class = AcademicClass.objects.get(school=school, name__iexact=class_name)
        section = Section.objects.get(academic_class=academic_class, name__iexact=section_name)

        student_username = row.get('student_username', '').strip() or f"student_{school.id}_{index}"
        if User.objects.filter(username=student_username).exists():
            student_username = f"{student_username}_{index}"

        student_user = User.objects.create_user(
            username=student_username, password=f"pass@{parent_phone}", role='STUDENT',
        )
        student_profile = StudentProfile.objects.create(
            user=student_user, school=school, name=student_name,
            academic_class=academic_class, section=section,
            roll_number=row.get('roll_number', '').strip(),
            admission_number=row.get('admission_number', '').strip(),
        )

        parent_profile = ParentProfile.objects.filter(school=school, user__phone_number=parent_phone).first()
        if parent_profile is None:
            parent_username = row.get('parent_username', '').strip() or f"parent_{school.id}_{parent_phone}"
            if User.objects.filter(username=parent_username).exists():
                parent_username = f"{parent_username}_{index}"
            parent_user = User.objects.create_user(
                username=parent_username, password=f"pass@{parent_phone}", role='PARENT',
                phone_number=parent_phone,
            )
            parent_profile = ParentProfile.objects.create(
                user=parent_user, school=school, name=parent_name,
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

    def get_student_upload_rows(self, batch_id):
        return list(
            StudentBulkUploadRow.objects.filter(batch_id=batch_id).order_by('row_number')
        )

    def create_teacher_bulk_upload_batch(self, school, principal_profile, csv_file):
        return TeacherBulkUploadBatch.objects.create(
            school=school, uploaded_by=principal_profile.user, csv_file=csv_file,
        )

    def process_teacher_bulk_upload(self, batch, school):
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
            row_obj = TeacherBulkUploadRow.objects.create(batch=batch, row_number=i, raw_data=dict(row))
            try:
                with transaction.atomic():
                    self._process_teacher_upload_row(row, school, row_obj, i)
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

    def _process_teacher_upload_row(self, row, school, row_obj, index):
        name = row.get('name', '').strip()
        phone_number = row.get('phone_number', '').strip()
        username = row.get('username', '').strip()
        password = row.get('password', '').strip()

        if not all([name, phone_number, username, password]):
            raise ValueError('Missing required fields.')

        if User.objects.filter(username=username).exists():
            raise ValueError('Username already exists.')

        primary_subject = None
        primary_subject_id = row.get('primary_subject_id', '').strip()
        if primary_subject_id:
            try:
                primary_subject = Subject.objects.get(id=primary_subject_id, school=school)
            except Subject.DoesNotExist:
                raise ValueError('Primary subject not found.')

        teacher_user = User.objects.create_user(
            username=username, password=password, role='TEACHER', phone_number=phone_number
        )
        teacher_profile = TeacherProfile.objects.create(
            user=teacher_user, school=school, name=name, primary_subject=primary_subject
        )

        assigned_section_ids_str = row.get('assigned_section_ids', '').strip()
        if assigned_section_ids_str:
            section_ids = [s.strip() for s in assigned_section_ids_str.split(',') if s.strip()]
            sections = list(Section.objects.filter(id__in=section_ids, school=school))
            if len(sections) != len(section_ids):
                raise ValueError('One or more sections not found.')
            teacher_profile.assigned_sections.set(sections)

        row_obj.status = UPLOAD_ROW_STATUS_SUCCESS
        row_obj.created_teacher = teacher_profile
        row_obj.save()

    def get_teacher_bulk_upload_batch(self, batch_id, school_id):
        try:
            return TeacherBulkUploadBatch.objects.get(id=batch_id, school_id=school_id)
        except TeacherBulkUploadBatch.DoesNotExist:
            return None

    def get_teacher_upload_rows(self, batch_id):
        return list(
            TeacherBulkUploadRow.objects.filter(batch_id=batch_id).order_by('row_number')
        )

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

    def get_calendar_event(self, event_id, school_id):
        try:
            return AcademicCalendarEvent.objects.get(id=event_id, school_id=school_id)
        except AcademicCalendarEvent.DoesNotExist:
            return None

    def update_calendar_event(self, event, updates):
        for key, value in updates.items():
            setattr(event, key, value)
        event.save()
        return event

    def delete_calendar_event(self, event):
        event.delete()

    # --- Attendance ---

    def get_academic_class_by_id(self, school_id, class_id):
        from core.exceptions import NotFoundException
        from principal.constants import CLASS_NOT_FOUND
        try:
            return AcademicClass.objects.get(id=class_id, school_id=school_id)
        except AcademicClass.DoesNotExist:
            raise NotFoundException(CLASS_NOT_FOUND)

    def get_daily_class_attendance_summary(self, school_id, date):
        students = list(
            StudentProfile.objects.filter(school_id=school_id, is_active=True)
            .select_related('academic_class')
            .order_by('academic_class__display_order', 'academic_class__name')
        )

        present_ids = set(
            StudentAttendance.objects.filter(
                session__school_id=school_id,
                session__date=date,
                session__confirmed_at__isnull=False,
                status=ATTENDANCE_STATUS_PRESENT,
            ).values_list('student_id', flat=True)
        )

        class_map = {}
        for student in students:
            cls = student.academic_class
            if cls.id not in class_map:
                class_map[cls.id] = {
                    'class_id': cls.id,
                    'class_name': cls.name,
                    'display_order': cls.display_order,
                    'total_students': 0,
                    'present_count': 0,
                }
            class_map[cls.id]['total_students'] += 1
            if student.id in present_ids:
                class_map[cls.id]['present_count'] += 1

        return sorted(class_map.values(), key=lambda x: (x['display_order'], x['class_name']))

    def get_class_attendance_detail(self, school_id, class_id, date):
        sections = list(
            Section.objects.filter(school_id=school_id, academic_class_id=class_id)
            .order_by('name')
        )

        students = list(
            StudentProfile.objects.filter(
                school_id=school_id, academic_class_id=class_id, is_active=True
            )
            .select_related('section')
            .order_by('section__name', 'name')
        )

        records = StudentAttendance.objects.filter(
            session__school_id=school_id,
            session__section__academic_class_id=class_id,
            session__date=date,
            session__confirmed_at__isnull=False,
        ).values('student_id', 'status')

        student_status = {}
        for rec in records:
            sid = rec['student_id']
            if sid not in student_status or student_status[sid] != ATTENDANCE_STATUS_PRESENT:
                student_status[sid] = rec['status']

        section_map = {
            s.id: {
                'section_id': s.id,
                'section_name': s.name,
                'total_students': 0,
                'present_students': [],
                'absent_students': [],
            }
            for s in sections
        }

        for student in students:
            sec_id = student.section_id
            if sec_id not in section_map:
                continue
            section_map[sec_id]['total_students'] += 1
            status = student_status.get(student.id)
            if status == ATTENDANCE_STATUS_PRESENT:
                section_map[sec_id]['present_students'].append(student)
            elif status is not None:
                section_map[sec_id]['absent_students'].append(student)

        return [section_map[s.id] for s in sections]

    # --- Classes, Subjects, Sections CRUD ---

    def create_class(self, school, name, display_order=0):
        return AcademicClass.objects.create(school=school, name=name, display_order=display_order)

    def update_class(self, academic_class, name=None, display_order=None):
        if name is not None:
            academic_class.name = name
        if display_order is not None:
            academic_class.display_order = display_order
        academic_class.save(update_fields=['name', 'display_order', 'updated_at'])
        return academic_class

    def delete_class(self, academic_class):
        academic_class.delete()

    def get_admin_subject_by_id(self, subject_id, school_id):
        try:
            return Subject.objects.get(id=subject_id, school_id=school_id)
        except Subject.DoesNotExist:
            return None

    def create_subject(self, school, name, code='', is_active=True):
        return Subject.objects.create(school=school, name=name, code=code, is_active=is_active)

    def update_subject(self, subject, name=None, code=None, is_active=None):
        update_fields = ['updated_at']
        if name is not None:
            subject.name = name
            update_fields.append('name')
        if code is not None:
            subject.code = code
            update_fields.append('code')
        if is_active is not None:
            subject.is_active = is_active
            update_fields.append('is_active')
        subject.save(update_fields=update_fields)
        return subject

    def delete_subject(self, subject):
        subject.delete()

    def create_section(self, school, academic_class, name, class_teacher=None, parent_query_enabled=True):
        return Section.objects.create(
            school=school, academic_class=academic_class, name=name,
            class_teacher=class_teacher, parent_query_enabled=parent_query_enabled
        )

    def update_section(self, section, name=None, class_teacher=None, parent_query_enabled=None, clear_class_teacher=False):
        update_fields = ['updated_at']
        if name is not None:
            section.name = name
            update_fields.append('name')
        if class_teacher is not None:
            section.class_teacher = class_teacher
            update_fields.append('class_teacher_id')
        elif clear_class_teacher:
            section.class_teacher = None
            update_fields.append('class_teacher_id')
            
        if parent_query_enabled is not None:
            section.parent_query_enabled = parent_query_enabled
            update_fields.append('parent_query_enabled')
        section.save(update_fields=update_fields)
        return section

    def delete_section(self, section):
        section.delete()
