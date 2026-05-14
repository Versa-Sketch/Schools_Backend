from django.utils import timezone
from django.utils.dateparse import parse_date

from core.exceptions import NotFoundException, PermissionDeniedException, ValidationException


def _require_school(profile):
    if profile is None:
        raise NotFoundException('No school associated with this user.')
    school = getattr(profile, 'school', None)
    if school is None:
        raise NotFoundException('No school associated with this user.')
    return school


class ClassListInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def get_classes(self, user):
        profile = self.storage.get_user_profile(user)
        school = _require_school(profile)
        classes = self.storage.get_classes_for_user(user=user, profile=profile, school_id=school.id)
        return self.presenter.class_list_success(classes=classes)


class SectionListInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def get_sections(self, user, class_id=None):
        profile = self.storage.get_user_profile(user)
        school = _require_school(profile)
        sections = self.storage.get_sections_for_user(
            user=user, profile=profile, school_id=school.id, class_id=class_id
        )
        return self.presenter.section_list_success(sections=sections)


class SectionStudentsInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def get_students(self, user, section_id):
        profile = self.storage.get_user_profile(user)
        school = _require_school(profile)
        if not self.storage.can_access_section(user, profile, section_id, school.id):
            raise PermissionDeniedException('You do not have access to this section.')
        students = self.storage.get_students_for_section_user(
            user=user, profile=profile, section_id=section_id, school_id=school.id
        )
        return self.presenter.student_list_success(students=students)


class StudentDetailInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def get_student(self, user, student_id, date=None):
        profile = self.storage.get_user_profile(user)
        school = _require_school(profile)
        attendance_date = parse_date(date) if date else timezone.localdate()
        if attendance_date is None:
            raise ValidationException('Invalid date format. Use YYYY-MM-DD.')

        student = self.storage.get_student_by_id(student_id, school.id)
        if student is None:
            raise NotFoundException('Student not found.')
        if not self.storage.can_access_student(user, profile, student, school.id):
            raise PermissionDeniedException('You do not have access to this student.')

        attendance_records = self.storage.get_student_attendance_for_date(student, attendance_date)
        return self.presenter.student_detail_success(
            student=student,
            date=attendance_date,
            attendance_records=attendance_records,
        )


class SubjectListInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def get_subjects(self, user):
        profile = self.storage.get_user_profile(user)
        school = _require_school(profile)
        subjects = self.storage.get_subjects_for_school(school_id=school.id)
        return self.presenter.subject_list_success(subjects=subjects)
