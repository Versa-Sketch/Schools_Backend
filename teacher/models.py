from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from core.models import ROLE_TEACHER


class TeacherProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    school = models.ForeignKey(
        'core.School',
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=255)
    mobile_number = models.CharField(max_length=20)
    primary_subject = models.ForeignKey(
        'core.Subject',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    assigned_sections = models.ManyToManyField(
        'core.Section',
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def clean(self):
        errors = {}
        if self.user_id and self.user.role != ROLE_TEACHER:
            errors['user'] = 'Teacher profile requires a teacher user role.'
        if self.primary_subject_id and self.school_id and self.primary_subject.school_id != self.school_id:
            errors['primary_subject'] = 'Primary subject must belong to the same school.'
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return self.name
