from django.conf import settings
from django.db import models


class StudentProfile(models.Model):
    user = models.OneToOneField(
        'core.User',
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

    def __str__(self):
        return self.name
