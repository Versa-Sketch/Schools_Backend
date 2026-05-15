from core.exceptions import NotFoundException, ValidationException
from .base import _ensure_principal


class AssignTeacherSectionsInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def assign_sections(self, user, teacher_id, data):
        _ensure_principal(user)
        principal = self.storage.get_principal_profile(user)

        subject_id = data.get('subject_id')
        section_ids = data.get('section_ids')

        if not subject_id or section_ids is None:
            raise ValidationException('subject_id and section_ids are required.')
        if not isinstance(section_ids, list) or len(section_ids) == 0:
            raise ValidationException('section_ids must be a non-empty list.')

        school_id = principal.school_id

        teacher = self.storage.get_teacher_by_id(teacher_id, school_id)
        if teacher is None:
            raise NotFoundException('Teacher not found.')

        subject = self.storage.get_subject_by_id(subject_id, school_id)
        if subject is None:
            raise ValidationException('Subject not found.')

        sections = self.storage.get_sections_by_ids(section_ids, school_id)
        found_ids = {str(s.id) for s in sections}
        invalid_ids = [sid for sid in section_ids if str(sid) not in found_ids]
        if invalid_ids:
            raise ValidationException(f'Invalid section IDs: {invalid_ids}')

        teacher = self.storage.assign_teacher_sections(teacher, subject, sections)
        return self.presenter.assign_success(teacher=teacher)
