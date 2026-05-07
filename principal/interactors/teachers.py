from core.exceptions import NotFoundException, ValidationException
from principal import constants
from .base import _ensure_principal


class ListTeachersInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def list_teachers(self, user, subject_id=None, section_id=None, search=None):
        _ensure_principal(user)
        profile = self.storage.get_principal_profile(user)
        if profile is None:
            raise NotFoundException('Principal profile not found.')
        teachers = self.storage.get_teachers_for_school(
            school_id=profile.school_id,
            subject_id=subject_id,
            section_id=section_id,
            search=search,
        )
        return self.presenter.teacher_list_success(teachers=teachers)


class CreateTeacherInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def create_teacher(self, user, data):
        _ensure_principal(user)
        profile = self.storage.get_principal_profile(user)
        if profile is None:
            raise NotFoundException('Principal profile not found.')
        school = profile.school

        name = data.get('name', '').strip()
        mobile_number = data.get('mobile_number', '').strip()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        primary_subject_id = data.get('primary_subject_id')
        section_ids = data.get('assigned_section_ids', [])

        if not all([name, mobile_number, username, password]):
            raise ValidationException('name, mobile_number, username, and password are required.')
        if self.storage.username_exists(username):
            raise ValidationException(constants.USERNAME_ALREADY_EXISTS)

        primary_subject = None
        if primary_subject_id:
            primary_subject = self.storage.get_subject_by_id(primary_subject_id, school.id)
            if primary_subject is None:
                raise ValidationException(constants.SUBJECT_NOT_FOUND)

        sections = []
        if section_ids:
            sections = self.storage.get_sections_by_ids(section_ids, school.id)
            if len(sections) != len(section_ids):
                raise ValidationException(constants.SECTION_NOT_FOUND)

        teacher = self.storage.create_teacher(
            school=school, name=name, mobile_number=mobile_number,
            username=username, password=password,
            primary_subject=primary_subject, sections=sections,
        )
        return self.presenter.teacher_detail_success(teacher=teacher)


class UpdateTeacherInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def update_teacher(self, user, teacher_id, data):
        _ensure_principal(user)
        profile = self.storage.get_principal_profile(user)
        if profile is None:
            raise NotFoundException('Principal profile not found.')
        school = profile.school

        teacher = self.storage.get_teacher_by_id(teacher_id, school.id)
        if teacher is None:
            raise NotFoundException(constants.TEACHER_NOT_FOUND)

        updates = {}
        if 'name' in data:
            updates['name'] = data['name']
        if 'mobile_number' in data:
            updates['mobile_number'] = data['mobile_number']
        if 'primary_subject_id' in data:
            pid = data['primary_subject_id']
            if pid is None:
                updates['primary_subject'] = None
            else:
                subj = self.storage.get_subject_by_id(pid, school.id)
                if subj is None:
                    raise ValidationException(constants.SUBJECT_NOT_FOUND)
                updates['primary_subject'] = subj

        sections = None
        if 'assigned_section_ids' in data:
            section_ids = data['assigned_section_ids']
            sections = self.storage.get_sections_by_ids(section_ids, school.id)
            if len(sections) != len(section_ids):
                raise ValidationException(constants.SECTION_NOT_FOUND)

        teacher = self.storage.update_teacher(teacher, updates, sections=sections)
        return self.presenter.teacher_detail_success(teacher=teacher)
