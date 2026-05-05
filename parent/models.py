from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from core.models import ROLE_PARENT


class ParentProfile(models.Model):
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
    students = models.ManyToManyField(
        'student.StudentProfile',
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def clean(self):
        if self.user_id and self.user.role != ROLE_PARENT:
            raise ValidationError({'user': 'Parent profile requires a parent user role.'})

    def __str__(self):
        return self.name
