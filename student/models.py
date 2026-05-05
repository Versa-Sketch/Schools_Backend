from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from core.models import ROLE_STUDENT


class StudentProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    school = models.ForeignKey(
        'core.School',
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=255)
    academic_class = models.ForeignKey(
        'core.AcademicClass',
        on_delete=models.PROTECT,
    )
    section = models.ForeignKey(
        'core.Section',
        on_delete=models.PROTECT,
    )
    roll_number = models.CharField(max_length=30, blank=True)
    admission_number = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['school', 'admission_number'],
                condition=~models.Q(admission_number=''),
                name='unique_student_admission_number_per_school_when_set',
            ),
            models.UniqueConstraint(
                fields=['section', 'roll_number'],
                condition=~models.Q(roll_number=''),
                name='unique_student_roll_number_per_section_when_set',
            ),
        ]

    def clean(self):
        errors = {}
        if self.user_id and self.user.role != ROLE_STUDENT:
            errors['user'] = 'Student profile requires a student user role.'
        if self.academic_class_id and self.school_id and self.academic_class.school_id != self.school_id:
            errors['academic_class'] = 'Class must belong to the same school.'
        if self.section_id and self.school_id and self.section.school_id != self.school_id:
            errors['section'] = 'Section must belong to the same school.'
        if self.section_id and self.academic_class_id and self.section.academic_class_id != self.academic_class_id:
            errors['section'] = 'Section must belong to the selected class.'
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return self.name
