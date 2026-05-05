from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from core.models import ROLE_PRINCIPAL


class PrincipalProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    school = models.ForeignKey(
        'core.School',
        on_delete=models.CASCADE,
    )
    mobile_number = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['user__username']

    def clean(self):
        if self.user_id and self.user.role != ROLE_PRINCIPAL:
            raise ValidationError({'user': 'Principal profile requires a principal user role.'})

    def __str__(self):
        return f'{self.user.get_full_name() or self.user.username} - {self.school}'
