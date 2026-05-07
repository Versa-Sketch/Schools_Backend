import uuid

from django.conf import settings
from django.db import models

from core.models import AcademicClass, School, Section, TimeStampedModel

from .constants import (
    ANALYTICS_STATUS_CHOICES,
    ANALYTICS_STATUS_PENDING,
    DIFFICULTY_CHOICES,
    PERFORMANCE_CHOICES,
    QUESTION_STATUS_CHOICES,
    RISK_CHOICES,
    SUBJECT_CHOICES,
)


class AnalyticsExam(TimeStampedModel):
    """One per CSV upload — may span multiple sections of the same exam event."""

    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='analytics_exams')
    exam_name = models.CharField(max_length=255)
    exam_date = models.DateField()
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='uploaded_exams',
    )
    analytics_status = models.CharField(
        max_length=10,
        choices=ANALYTICS_STATUS_CHOICES,
        default=ANALYTICS_STATUS_PENDING,
    )

    class Meta:
        ordering = ['-exam_date', '-created_at']

    def __str__(self):
        return f'{self.exam_name} ({self.exam_date})'


class AnalyticsStudent(models.Model):
    """Student identified by enrollment number from the CSV.

    Linked to core.Section via FK when section exists in the system.
    Text fallback fields always populated for resilience.
    linked_user is set later to allow STUDENT/PARENT role access.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student_ref_id = models.CharField(max_length=50)
    name = models.CharField(max_length=255)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='analytics_students')
    section = models.ForeignKey(
        Section,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='analytics_students',
    )
    academic_class = models.ForeignKey(
        AcademicClass,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='analytics_students',
    )
    class_name = models.CharField(max_length=20)
    section_name = models.CharField(max_length=10)
    linked_user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='analytics_student',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['student_ref_id', 'school'],
                name='unique_student_ref_per_school',
            ),
        ]

    def __str__(self):
        return f'{self.name} ({self.student_ref_id})'


class ExamSubject(models.Model):
    """MATHS, PHYSICS, or CHEMISTRY row for a given exam — 3 rows per AnalyticsExam."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    exam = models.ForeignKey(AnalyticsExam, on_delete=models.CASCADE, related_name='subjects')
    subject_name = models.CharField(max_length=20, choices=SUBJECT_CHOICES)
    total_questions = models.PositiveSmallIntegerField()
    max_marks = models.PositiveSmallIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['exam', 'subject_name'],
                name='unique_subject_per_exam',
            ),
        ]

    def __str__(self):
        return f'{self.subject_name} – {self.exam.exam_name}'


class ExamResult(models.Model):
    """One row per student × subject × exam. Stores marks and C/W/U summary."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    exam = models.ForeignKey(AnalyticsExam, on_delete=models.CASCADE, related_name='results')
    student = models.ForeignKey(
        AnalyticsStudent, on_delete=models.CASCADE, related_name='results'
    )
    subject = models.ForeignKey(ExamSubject, on_delete=models.CASCADE, related_name='results')
    total_marks = models.IntegerField()
    exam_rank = models.PositiveIntegerField()
    correct = models.PositiveSmallIntegerField()
    wrong = models.PositiveSmallIntegerField()
    unattempted = models.PositiveSmallIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['exam', 'student', 'subject'],
                name='unique_result_per_student_subject_exam',
            ),
        ]

    def __str__(self):
        return f'{self.student.name} – {self.subject.subject_name} – {self.total_marks}'


class QuestionResult(models.Model):
    """One row per student × question. Status is C, W, or U."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    exam = models.ForeignKey(
        AnalyticsExam, on_delete=models.CASCADE, related_name='question_results'
    )
    student = models.ForeignKey(
        AnalyticsStudent, on_delete=models.CASCADE, related_name='question_results'
    )
    subject = models.ForeignKey(
        ExamSubject, on_delete=models.CASCADE, related_name='question_results'
    )
    q_no = models.PositiveSmallIntegerField()
    status = models.CharField(max_length=1, choices=QUESTION_STATUS_CHOICES)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['exam', 'student', 'subject', 'q_no'],
                name='unique_question_result_per_student',
            ),
        ]
        indexes = [
            models.Index(fields=['exam', 'subject', 'q_no']),
            models.Index(fields=['exam', 'student']),
        ]

    def __str__(self):
        return f'Q{self.q_no} {self.subject.subject_name} – {self.student.name}: {self.status}'


class QuestionAnalytics(models.Model):
    """Pre-computed analytics per question. Recomputed after every upload."""

    exam = models.ForeignKey(
        AnalyticsExam, on_delete=models.CASCADE, related_name='question_analytics'
    )
    subject = models.ForeignKey(
        ExamSubject, on_delete=models.CASCADE, related_name='question_analytics'
    )
    q_no = models.PositiveSmallIntegerField()
    correct_count = models.PositiveIntegerField(default=0)
    wrong_count = models.PositiveIntegerField(default=0)
    skip_count = models.PositiveIntegerField(default=0)
    difficulty_index = models.FloatField(default=0.0)
    difficulty_tag = models.CharField(max_length=6, choices=DIFFICULTY_CHOICES, default='HARD')
    discrimination_index = models.FloatField(default=0.0)
    has_key_error = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['exam', 'subject', 'q_no'],
                name='unique_question_analytics',
            ),
        ]

    def __str__(self):
        return f'Q{self.q_no} {self.subject.subject_name} [{self.difficulty_tag}]'


class SectionAnalytics(models.Model):
    """Pre-computed per section × subject × exam.

    Only created when the section has a matching FK in core.Section.
    """

    exam = models.ForeignKey(
        AnalyticsExam, on_delete=models.CASCADE, related_name='section_analytics'
    )
    section = models.ForeignKey(
        Section, on_delete=models.CASCADE, related_name='section_analytics'
    )
    academic_class = models.ForeignKey(
        AcademicClass, on_delete=models.CASCADE, related_name='section_analytics'
    )
    subject = models.ForeignKey(
        ExamSubject, on_delete=models.CASCADE, related_name='section_analytics'
    )
    avg_marks = models.FloatField(default=0.0)
    median_marks = models.FloatField(default=0.0)
    std_dev = models.FloatField(default=0.0)
    top_scorer = models.ForeignKey(
        AnalyticsStudent,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='topped_sections',
    )
    at_risk_count = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['exam', 'section', 'subject'],
                name='unique_section_analytics',
            ),
        ]

    def __str__(self):
        return f'{self.section} – {self.subject.subject_name} – {self.exam.exam_name}'


class StudentRisk(models.Model):
    """Pre-computed risk and performance labels per student × subject × exam."""

    exam = models.ForeignKey(AnalyticsExam, on_delete=models.CASCADE, related_name='student_risks')
    student = models.ForeignKey(
        AnalyticsStudent, on_delete=models.CASCADE, related_name='risk_scores'
    )
    subject = models.ForeignKey(
        ExamSubject, on_delete=models.CASCADE, related_name='student_risks'
    )
    z_score = models.FloatField(default=0.0)
    risk_score = models.FloatField(default=0.0)
    risk_label = models.CharField(max_length=5, choices=RISK_CHOICES, default='SAFE')
    performance_label = models.CharField(
        max_length=20, choices=PERFORMANCE_CHOICES, default='AVERAGE'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['exam', 'student', 'subject'],
                name='unique_student_risk',
            ),
        ]

    def __str__(self):
        return (
            f'{self.student.name} – {self.subject.subject_name} '
            f'[{self.risk_label} / {self.performance_label}]'
        )
