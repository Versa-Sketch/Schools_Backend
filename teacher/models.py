from django.conf import settings
from django.db import models


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

    def __str__(self):
        return self.name
