from django.conf import settings
from django.db import models


class PrincipalProfile(models.Model):
    user = models.OneToOneField(
        'core.User',
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

    def __str__(self):
        return f'{self.user.get_full_name() or self.user.username} - {self.school}'
