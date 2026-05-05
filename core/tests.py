from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from core.models import (
    ATTENDANCE_ONCE,
    ATTENDANCE_SLOT_AFTERNOON,
    ATTENDANCE_SLOT_MORNING,
    ATTENDANCE_TWICE,
    ROLE_PARENT,
    ROLE_PRINCIPAL,
    ROLE_STUDENT,
    ROLE_TEACHER,
    UPLOAD_ROW_STATUS_FAILED,
    UPLOAD_ROW_STATUS_SUCCESS,
    AcademicClass,
    AttendanceSession,
    Homework,
    ParentQuery,
    School,
    SchoolConfiguration,
    Section,
    StudentBulkUploadBatch,
    StudentBulkUploadRow,
    Subject,
)
from parent.models import ParentProfile
from principal.models import PrincipalProfile
from student.models import StudentProfile
from teacher.models import TeacherProfile

User = get_user_model()


class SchoolModelTests(TestCase):
    def test_core_school_structure_can_be_created(self):
        school = School.objects.create(name='Green Valley School', subdomain='green-valley')
        SchoolConfiguration.objects.create(school=school)
        academic_class = AcademicClass.objects.create(school=school, name='Class 1', display_order=1)
        subject = Subject.objects.create(school=school, name='Math', code='MATH')
        section = Section.objects.create(school=school, academic_class=academic_class, name='A')

        self.assertEqual(str(school), 'Green Valley School')
        self.assertEqual(section.academic_class, academic_class)
        self.assertEqual(subject.school, school)

    def test_duplicate_school_subdomain_is_rejected(self):
        School.objects.create(name='One', subdomain='same')

        with self.assertRaises(IntegrityError):
            School.objects.create(name='Two', subdomain='same')

    def test_duplicate_section_name_in_same_class_is_rejected(self):
        school = School.objects.create(name='Green Valley School', subdomain='green-valley')
        academic_class = AcademicClass.objects.create(school=school, name='Class 1')
        Section.objects.create(school=school, academic_class=academic_class, name='A')

        with self.assertRaises(IntegrityError):
            Section.objects.create(school=school, academic_class=academic_class, name='A')


class RoleProfileTests(TestCase):
    def test_role_profiles_can_be_created_and_linked(self):
        school = School.objects.create(name='Green Valley School', subdomain='green-valley')
        academic_class = AcademicClass.objects.create(school=school, name='Class 1')
        subject = Subject.objects.create(school=school, name='Math')
        section = Section.objects.create(school=school, academic_class=academic_class, name='A')
        principal = PrincipalProfile.objects.create(
            user=User.objects.create_user(username='principal', role=ROLE_PRINCIPAL),
            school=school,
            mobile_number='9000000000',
        )
        teacher = TeacherProfile.objects.create(
            user=User.objects.create_user(username='teacher', role=ROLE_TEACHER),
            school=school,
            name='Teacher One',
            mobile_number='9000000001',
            primary_subject=subject,
        )
        teacher.assigned_sections.add(section)
        student = StudentProfile.objects.create(
            user=User.objects.create_user(username='student', role=ROLE_STUDENT),
            school=school,
            name='Student One',
            academic_class=academic_class,
            section=section,
            admission_number='ADM001',
        )
        parent = ParentProfile.objects.create(
            user=User.objects.create_user(username='parent', role=ROLE_PARENT),
            school=school,
            name='Parent One',
            mobile_number='9000000002',
        )
        parent.students.add(student)

        self.assertEqual(principal.school, school)
        self.assertIn(section, teacher.assigned_sections.all())
        self.assertIn(student, parent.students.all())

    def test_role_profile_rejects_wrong_user_role(self):
        school = School.objects.create(name='Green Valley School', subdomain='green-valley')
        profile = TeacherProfile(
            user=User.objects.create_user(username='not-a-teacher', role=ROLE_PARENT),
            school=school,
            name='Teacher One',
            mobile_number='9000000001',
        )

        with self.assertRaises(ValidationError):
            profile.full_clean()


class AttendanceModelTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name='Green Valley School', subdomain='green-valley')
        self.config = SchoolConfiguration.objects.create(school=self.school)
        self.academic_class = AcademicClass.objects.create(school=self.school, name='Class 1')
        self.subject = Subject.objects.create(school=self.school, name='Math')
        self.section = Section.objects.create(school=self.school, academic_class=self.academic_class, name='A')
        self.teacher = TeacherProfile.objects.create(
            user=User.objects.create_user(username='teacher', role=ROLE_TEACHER),
            school=self.school,
            name='Teacher One',
            mobile_number='9000000001',
            primary_subject=self.subject,
        )
        self.teacher.assigned_sections.add(self.section)

    def test_duplicate_attendance_session_is_rejected(self):
        AttendanceSession.objects.create(
            school=self.school,
            section=self.section,
            date=timezone.localdate(),
            slot=ATTENDANCE_SLOT_MORNING,
            taken_by=self.teacher,
        )

        with self.assertRaises(IntegrityError):
            AttendanceSession.objects.create(
                school=self.school,
                section=self.section,
                date=timezone.localdate(),
                slot=ATTENDANCE_SLOT_MORNING,
                taken_by=self.teacher,
            )

    def test_once_per_day_config_rejects_afternoon_slot(self):
        self.config.attendance_frequency = ATTENDANCE_ONCE
        self.config.save()
        session = AttendanceSession(
            school=self.school,
            section=self.section,
            date=timezone.localdate(),
            slot=ATTENDANCE_SLOT_AFTERNOON,
            taken_by=self.teacher,
        )

        with self.assertRaises(ValidationError):
            session.full_clean()

    def test_twice_per_day_config_allows_afternoon_slot(self):
        self.config.attendance_frequency = ATTENDANCE_TWICE
        self.config.save()
        session = AttendanceSession(
            school=self.school,
            section=self.section,
            date=timezone.localdate(),
            slot=ATTENDANCE_SLOT_AFTERNOON,
            taken_by=self.teacher,
        )

        session.full_clean()


class WorkflowValidationTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name='Green Valley School', subdomain='green-valley')
        self.config = SchoolConfiguration.objects.create(school=self.school)
        self.academic_class = AcademicClass.objects.create(school=self.school, name='Class 1')
        self.subject = Subject.objects.create(school=self.school, name='Math')
        self.section = Section.objects.create(school=self.school, academic_class=self.academic_class, name='A')
        self.teacher = TeacherProfile.objects.create(
            user=User.objects.create_user(username='teacher', role=ROLE_TEACHER),
            school=self.school,
            name='Teacher One',
            mobile_number='9000000001',
            primary_subject=self.subject,
        )
        self.teacher.assigned_sections.add(self.section)
        self.student = StudentProfile.objects.create(
            user=User.objects.create_user(username='student', role=ROLE_STUDENT),
            school=self.school,
            name='Student One',
            academic_class=self.academic_class,
            section=self.section,
            admission_number='ADM001',
        )
        self.parent = ParentProfile.objects.create(
            user=User.objects.create_user(username='parent', role=ROLE_PARENT),
            school=self.school,
            name='Parent One',
            mobile_number='9000000002',
        )
        self.parent.students.add(self.student)

    def test_teacher_must_be_assigned_to_homework_section(self):
        other_teacher = TeacherProfile.objects.create(
            user=User.objects.create_user(username='other-teacher', role=ROLE_TEACHER),
            school=self.school,
            name='Teacher Two',
            mobile_number='9000000003',
            primary_subject=self.subject,
        )
        homework = Homework(
            school=self.school,
            section=self.section,
            subject=self.subject,
            assigned_by=other_teacher,
            description='Read chapter 1',
            deadline=timezone.now(),
        )

        with self.assertRaises(ValidationError):
            homework.full_clean()

    def test_bulk_upload_rows_track_success_and_failure(self):
        principal = PrincipalProfile.objects.create(
            user=User.objects.create_user(username='principal', role=ROLE_PRINCIPAL),
            school=self.school,
            mobile_number='9000000004',
        )
        batch = StudentBulkUploadBatch.objects.create(
            school=self.school,
            uploaded_by=principal,
            csv_file='student_uploads/sample.csv',
            total_rows=2,
            success_count=1,
            error_count=1,
        )
        StudentBulkUploadRow.objects.create(
            batch=batch,
            row_number=1,
            raw_data={'Student Name': 'Student One'},
            status=UPLOAD_ROW_STATUS_SUCCESS,
            created_student=self.student,
            created_parent=self.parent,
        )
        StudentBulkUploadRow.objects.create(
            batch=batch,
            row_number=2,
            raw_data={'Student Name': ''},
            status=UPLOAD_ROW_STATUS_FAILED,
            error_message='Student Name is required.',
        )

        self.assertEqual(batch.studentbulkuploadrow_set.count(), 2)
        self.assertEqual(batch.studentbulkuploadrow_set.filter(status=UPLOAD_ROW_STATUS_FAILED).count(), 1)

    def test_parent_query_respects_school_configuration(self):
        self.config.parent_query_enabled = False
        self.config.save()
        query = ParentQuery(
            school=self.school,
            parent=self.parent,
            student=self.student,
            section=self.section,
            assigned_teacher=self.teacher,
            subject='Homework doubt',
            message='Please explain the homework.',
        )

        with self.assertRaises(ValidationError):
            query.full_clean()
