from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


ROLE_PRINCIPAL = 'PRINCIPAL'
ROLE_TEACHER = 'TEACHER'
ROLE_STUDENT = 'STUDENT'
ROLE_PARENT = 'PARENT'
ROLE_CHOICES = [
    (ROLE_PRINCIPAL, 'Principal'),
    (ROLE_TEACHER, 'Teacher'),
    (ROLE_STUDENT, 'Student'),
    (ROLE_PARENT, 'Parent'),
]

ATTENDANCE_ONCE = 'ONCE'
ATTENDANCE_TWICE = 'TWICE'
ATTENDANCE_FREQUENCY_CHOICES = [
    (ATTENDANCE_ONCE, 'Once per day'),
    (ATTENDANCE_TWICE, 'Twice per day'),
]

ATTENDANCE_SLOT_MORNING = 'MORNING'
ATTENDANCE_SLOT_AFTERNOON = 'AFTERNOON'
ATTENDANCE_SLOT_CHOICES = [
    (ATTENDANCE_SLOT_MORNING, 'Morning'),
    (ATTENDANCE_SLOT_AFTERNOON, 'Afternoon'),
]

ATTENDANCE_STATUS_PRESENT = 'PRESENT'
ATTENDANCE_STATUS_ABSENT = 'ABSENT'
ATTENDANCE_STATUS_CHOICES = [
    (ATTENDANCE_STATUS_PRESENT, 'Present'),
    (ATTENDANCE_STATUS_ABSENT, 'Absent'),
]

NOTIFICATION_CHANNEL_WHATSAPP = 'WHATSAPP'
NOTIFICATION_CHANNEL_CHOICES = [
    (NOTIFICATION_CHANNEL_WHATSAPP, 'WhatsApp'),
]

NOTIFICATION_STATUS_PENDING = 'PENDING'
NOTIFICATION_STATUS_SENT = 'SENT'
NOTIFICATION_STATUS_FAILED = 'FAILED'
NOTIFICATION_STATUS_CHOICES = [
    (NOTIFICATION_STATUS_PENDING, 'Pending'),
    (NOTIFICATION_STATUS_SENT, 'Sent'),
    (NOTIFICATION_STATUS_FAILED, 'Failed'),
]

AUTHOR_ROLE_PRINCIPAL = 'PRINCIPAL'
AUTHOR_ROLE_TEACHER = 'TEACHER'
AUTHOR_ROLE_CHOICES = [
    (AUTHOR_ROLE_PRINCIPAL, 'Principal'),
    (AUTHOR_ROLE_TEACHER, 'Teacher'),
]

ANNOUNCEMENT_AUDIENCE_SCHOOL = 'SCHOOL'
ANNOUNCEMENT_AUDIENCE_CLASS = 'CLASS'
ANNOUNCEMENT_AUDIENCE_SECTION = 'SECTION'
ANNOUNCEMENT_AUDIENCE_CHOICES = [
    (ANNOUNCEMENT_AUDIENCE_SCHOOL, 'School'),
    (ANNOUNCEMENT_AUDIENCE_CLASS, 'Class'),
    (ANNOUNCEMENT_AUDIENCE_SECTION, 'Section'),
]

UPLOAD_BATCH_STATUS_PENDING = 'PENDING'
UPLOAD_BATCH_STATUS_PROCESSING = 'PROCESSING'
UPLOAD_BATCH_STATUS_COMPLETED = 'COMPLETED'
UPLOAD_BATCH_STATUS_FAILED = 'FAILED'
UPLOAD_BATCH_STATUS_CHOICES = [
    (UPLOAD_BATCH_STATUS_PENDING, 'Pending'),
    (UPLOAD_BATCH_STATUS_PROCESSING, 'Processing'),
    (UPLOAD_BATCH_STATUS_COMPLETED, 'Completed'),
    (UPLOAD_BATCH_STATUS_FAILED, 'Failed'),
]

UPLOAD_ROW_STATUS_PENDING = 'PENDING'
UPLOAD_ROW_STATUS_SUCCESS = 'SUCCESS'
UPLOAD_ROW_STATUS_FAILED = 'FAILED'
UPLOAD_ROW_STATUS_CHOICES = [
    (UPLOAD_ROW_STATUS_PENDING, 'Pending'),
    (UPLOAD_ROW_STATUS_SUCCESS, 'Success'),
    (UPLOAD_ROW_STATUS_FAILED, 'Failed'),
]

CALENDAR_EVENT_TYPE_HOLIDAY = 'HOLIDAY'
CALENDAR_EVENT_TYPE_EXAM = 'EXAM'
CALENDAR_EVENT_TYPE_EVENT = 'EVENT'
CALENDAR_EVENT_TYPE_CHOICES = [
    (CALENDAR_EVENT_TYPE_HOLIDAY, 'Holiday'),
    (CALENDAR_EVENT_TYPE_EXAM, 'Exam'),
    (CALENDAR_EVENT_TYPE_EVENT, 'Event'),
]

PARENT_QUERY_STATUS_OPEN = 'OPEN'
PARENT_QUERY_STATUS_ANSWERED = 'ANSWERED'
PARENT_QUERY_STATUS_CLOSED = 'CLOSED'
PARENT_QUERY_STATUS_CHOICES = [
    (PARENT_QUERY_STATUS_OPEN, 'Open'),
    (PARENT_QUERY_STATUS_ANSWERED, 'Answered'),
    (PARENT_QUERY_STATUS_CLOSED, 'Closed'),
]


class User(AbstractUser):
    REQUIRED_FIELDS = ['role']

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class School(TimeStampedModel):
    name = models.CharField(max_length=255)
    subdomain = models.SlugField(max_length=100, unique=True)
    address = models.TextField(blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=20, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class SchoolConfiguration(TimeStampedModel):
    school = models.OneToOneField(
        School,
        on_delete=models.CASCADE,
    )
    attendance_frequency = models.CharField(
        max_length=5,
        choices=ATTENDANCE_FREQUENCY_CHOICES,
        default=ATTENDANCE_TWICE,
    )
    whatsapp_absent_automation_enabled = models.BooleanField(default=True)
    parent_query_enabled = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.school} configuration'


class AcademicClass(TimeStampedModel):
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=50)
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['display_order', 'name']
        constraints = [
            models.UniqueConstraint(
                fields=['school', 'name'],
                name='unique_class_name_per_school',
            ),
        ]

    def __str__(self):
        return f'{self.name} - {self.school}'


class Subject(TimeStampedModel):
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=30, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['school', 'name'],
                name='unique_subject_name_per_school',
            ),
            models.UniqueConstraint(
                fields=['school', 'code'],
                condition=~models.Q(code=''),
                name='unique_subject_code_per_school_when_set',
            ),
        ]

    def __str__(self):
        return self.name


class Section(TimeStampedModel):
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
    )
    academic_class = models.ForeignKey(
        AcademicClass,
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=20)
    class_teacher = models.ForeignKey(
        'teacher.TeacherProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ['academic_class__display_order', 'name']
        constraints = [
            models.UniqueConstraint(
                fields=['academic_class', 'name'],
                name='unique_section_name_per_class',
            ),
        ]

    def clean(self):
        errors = {}
        if self.academic_class_id and self.school_id and self.academic_class.school_id != self.school_id:
            errors['academic_class'] = 'Class must belong to the same school.'
        if self.class_teacher_id and self.school_id and self.class_teacher.school_id != self.school_id:
            errors['class_teacher'] = 'Class teacher must belong to the same school.'
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f'{self.academic_class.name} {self.name}'


class AttendanceSession(TimeStampedModel):
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
    )
    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
    )
    date = models.DateField()
    slot = models.CharField(
        max_length=10,
        choices=ATTENDANCE_SLOT_CHOICES,
        default=ATTENDANCE_SLOT_MORNING,
    )
    taken_by = models.ForeignKey(
        'teacher.TeacherProfile',
        on_delete=models.PROTECT,
    )
    confirmed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-date', 'slot']
        constraints = [
            models.UniqueConstraint(
                fields=['section', 'date', 'slot'],
                name='unique_attendance_session_per_section_date_slot',
            ),
        ]

    def clean(self):
        errors = {}
        if self.section_id and self.school_id and self.section.school_id != self.school_id:
            errors['section'] = 'Section must belong to the same school.'
        if self.taken_by_id and self.school_id and self.taken_by.school_id != self.school_id:
            errors['taken_by'] = 'Teacher must belong to the same school.'

        configuration = getattr(self.school, 'schoolconfiguration', None) if self.school_id else None
        if (
            self.slot == ATTENDANCE_SLOT_AFTERNOON
            and configuration
            and configuration.attendance_frequency == ATTENDANCE_ONCE
        ):
            errors['slot'] = 'Afternoon attendance requires twice-per-day attendance frequency.'
        if errors:
            raise ValidationError(errors)

    def confirm(self):
        self.confirmed_at = timezone.now()
        self.save(update_fields=['confirmed_at', 'updated_at'])

    def __str__(self):
        return f'{self.section} - {self.date} - {self.slot}'


class StudentAttendance(TimeStampedModel):
    session = models.ForeignKey(
        AttendanceSession,
        on_delete=models.CASCADE,
    )
    student = models.ForeignKey(
        'student.StudentProfile',
        on_delete=models.CASCADE,
    )
    status = models.CharField(
        max_length=7,
        choices=ATTENDANCE_STATUS_CHOICES,
    )

    class Meta:
        ordering = ['student__name']
        constraints = [
            models.UniqueConstraint(
                fields=['session', 'student'],
                name='unique_student_attendance_per_session',
            ),
        ]

    def clean(self):
        if self.session_id and self.student_id and self.session.school_id != self.student.school_id:
            raise ValidationError({'student': 'Student must belong to the same school as the attendance session.'})
        if self.session_id and self.student_id and self.session.section_id != self.student.section_id:
            raise ValidationError({'student': 'Student must belong to the attendance session section.'})

    def __str__(self):
        return f'{self.student} - {self.session} - {self.status}'


class AbsentNotificationLog(TimeStampedModel):
    attendance = models.ForeignKey(
        StudentAttendance,
        on_delete=models.CASCADE,
    )
    parent = models.ForeignKey(
        'parent.ParentProfile',
        on_delete=models.CASCADE,
    )
    channel = models.CharField(
        max_length=10,
        choices=NOTIFICATION_CHANNEL_CHOICES,
        default=NOTIFICATION_CHANNEL_WHATSAPP,
    )
    status = models.CharField(
        max_length=7,
        choices=NOTIFICATION_STATUS_CHOICES,
        default=NOTIFICATION_STATUS_PENDING,
    )
    provider_response = models.TextField(blank=True)
    error_message = models.TextField(blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    def clean(self):
        if self.attendance_id and self.attendance.status != ATTENDANCE_STATUS_ABSENT:
            raise ValidationError({'attendance': 'Notifications are logged only for absent attendance records.'})
        if self.attendance_id and self.parent_id and self.attendance.student.school_id != self.parent.school_id:
            raise ValidationError({'parent': 'Parent must belong to the same school as the student.'})
        if self.attendance_id and self.parent_id and not self.parent.students.filter(pk=self.attendance.student_id).exists():
            raise ValidationError({'parent': 'Parent must be linked to the absent student.'})

    def __str__(self):
        return f'{self.channel} notification for {self.attendance}'


class Announcement(TimeStampedModel):
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
    )
    author_role = models.CharField(max_length=10, choices=AUTHOR_ROLE_CHOICES)
    title = models.CharField(max_length=255)
    body = models.TextField()
    audience = models.CharField(max_length=7, choices=ANNOUNCEMENT_AUDIENCE_CHOICES)
    published_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-published_at', '-created_at']

    def __str__(self):
        return self.title


class AnnouncementTarget(TimeStampedModel):
    announcement = models.ForeignKey(
        Announcement,
        on_delete=models.CASCADE,
    )
    academic_class = models.ForeignKey(
        AcademicClass,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    def clean(self):
        errors = {}
        if not self.academic_class_id and not self.section_id:
            errors['academic_class'] = 'A class or section target is required.'
        if self.announcement_id and self.academic_class_id and self.academic_class.school_id != self.announcement.school_id:
            errors['academic_class'] = 'Target class must belong to the announcement school.'
        if self.announcement_id and self.section_id and self.section.school_id != self.announcement.school_id:
            errors['section'] = 'Target section must belong to the announcement school.'
        if self.section_id and self.academic_class_id and self.section.academic_class_id != self.academic_class_id:
            errors['section'] = 'Target section must belong to the selected class.'
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f'Target for {self.announcement}'


class AnnouncementAttachment(TimeStampedModel):
    announcement = models.ForeignKey(
        Announcement,
        on_delete=models.CASCADE,
    )
    file = models.FileField(upload_to='announcements/')
    filename = models.CharField(max_length=255, blank=True)
    content_type = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.filename or self.file.name


class StudyMaterial(TimeStampedModel):
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT)
    uploaded_by = models.ForeignKey(
        'teacher.TeacherProfile',
        on_delete=models.PROTECT,
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='study_materials/')
    material_date = models.DateField()

    class Meta:
        ordering = ['-material_date', '-created_at']

    def clean(self):
        errors = {}
        if self.section_id and self.school_id and self.section.school_id != self.school_id:
            errors['section'] = 'Section must belong to the same school.'
        if self.subject_id and self.school_id and self.subject.school_id != self.school_id:
            errors['subject'] = 'Subject must belong to the same school.'
        if self.uploaded_by_id and self.school_id and self.uploaded_by.school_id != self.school_id:
            errors['uploaded_by'] = 'Teacher must belong to the same school.'
        if self.uploaded_by_id and self.section_id and not self.uploaded_by.assigned_sections.filter(pk=self.section_id).exists():
            errors['uploaded_by'] = 'Teacher must be assigned to this section.'
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return self.title


class Homework(TimeStampedModel):
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT)
    assigned_by = models.ForeignKey(
        'teacher.TeacherProfile',
        on_delete=models.PROTECT,
    )
    description = models.TextField()
    deadline = models.DateTimeField()

    class Meta:
        ordering = ['deadline', '-created_at']

    def clean(self):
        errors = {}
        if self.section_id and self.school_id and self.section.school_id != self.school_id:
            errors['section'] = 'Section must belong to the same school.'
        if self.subject_id and self.school_id and self.subject.school_id != self.school_id:
            errors['subject'] = 'Subject must belong to the same school.'
        if self.assigned_by_id and self.school_id and self.assigned_by.school_id != self.school_id:
            errors['assigned_by'] = 'Teacher must belong to the same school.'
        if self.assigned_by_id and self.section_id and not self.assigned_by.assigned_sections.filter(pk=self.section_id).exists():
            errors['assigned_by'] = 'Teacher must be assigned to this section.'
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f'{self.subject} homework for {self.section}'


class StudentBulkUploadBatch(TimeStampedModel):
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    uploaded_by = models.ForeignKey(
        'principal.PrincipalProfile',
        on_delete=models.PROTECT,
    )
    csv_file = models.FileField(upload_to='student_uploads/')
    status = models.CharField(
        max_length=10,
        choices=UPLOAD_BATCH_STATUS_CHOICES,
        default=UPLOAD_BATCH_STATUS_PENDING,
    )
    total_rows = models.PositiveIntegerField(default=0)
    success_count = models.PositiveIntegerField(default=0)
    error_count = models.PositiveIntegerField(default=0)
    error_report = models.FileField(upload_to='student_upload_errors/', blank=True)

    class Meta:
        ordering = ['-created_at']

    def clean(self):
        if self.uploaded_by_id and self.school_id and self.uploaded_by.school_id != self.school_id:
            raise ValidationError({'uploaded_by': 'Principal must belong to the same school.'})

    def __str__(self):
        return f'Student upload for {self.school} ({self.status})'


class StudentBulkUploadRow(TimeStampedModel):
    batch = models.ForeignKey(
        StudentBulkUploadBatch,
        on_delete=models.CASCADE,
    )
    row_number = models.PositiveIntegerField()
    raw_data = models.JSONField(default=dict)
    status = models.CharField(
        max_length=7,
        choices=UPLOAD_ROW_STATUS_CHOICES,
        default=UPLOAD_ROW_STATUS_PENDING,
    )
    error_message = models.TextField(blank=True)
    created_student = models.ForeignKey(
        'student.StudentProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    created_parent = models.ForeignKey(
        'parent.ParentProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ['row_number']
        constraints = [
            models.UniqueConstraint(
                fields=['batch', 'row_number'],
                name='unique_student_upload_row_number_per_batch',
            ),
        ]

    def clean(self):
        errors = {}
        if self.created_student_id and self.created_student.school_id != self.batch.school_id:
            errors['created_student'] = 'Created student must belong to the batch school.'
        if self.created_parent_id and self.created_parent.school_id != self.batch.school_id:
            errors['created_parent'] = 'Created parent must belong to the batch school.'
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f'Row {self.row_number} - {self.status}'


class AcademicCalendarEvent(TimeStampedModel):
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    event_type = models.CharField(max_length=7, choices=CALENDAR_EVENT_TYPE_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    description = models.TextField(blank=True)
    visible_to = models.JSONField(default=list)

    class Meta:
        ordering = ['start_date', 'title']

    def clean(self):
        if self.end_date and self.start_date and self.end_date < self.start_date:
            raise ValidationError({'end_date': 'End date cannot be before start date.'})

    def __str__(self):
        return self.title


class ParentQuery(TimeStampedModel):
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    parent = models.ForeignKey('parent.ParentProfile', on_delete=models.CASCADE)
    student = models.ForeignKey('student.StudentProfile', on_delete=models.CASCADE)
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    assigned_teacher = models.ForeignKey(
        'teacher.TeacherProfile',
        on_delete=models.PROTECT,
    )
    subject = models.CharField(max_length=255)
    message = models.TextField()
    status = models.CharField(
        max_length=8,
        choices=PARENT_QUERY_STATUS_CHOICES,
        default=PARENT_QUERY_STATUS_OPEN,
    )

    class Meta:
        ordering = ['-created_at']

    def clean(self):
        errors = {}
        configuration = getattr(self.school, 'schoolconfiguration', None) if self.school_id else None
        if configuration and not configuration.parent_query_enabled:
            errors['school'] = 'Parent queries are disabled for this school.'
        if self.parent_id and self.school_id and self.parent.school_id != self.school_id:
            errors['parent'] = 'Parent must belong to the same school.'
        if self.student_id and self.school_id and self.student.school_id != self.school_id:
            errors['student'] = 'Student must belong to the same school.'
        if self.section_id and self.school_id and self.section.school_id != self.school_id:
            errors['section'] = 'Section must belong to the same school.'
        if self.assigned_teacher_id and self.school_id and self.assigned_teacher.school_id != self.school_id:
            errors['assigned_teacher'] = 'Teacher must belong to the same school.'
        if self.student_id and self.section_id and self.student.section_id != self.section_id:
            errors['student'] = 'Student must belong to the selected section.'
        if self.parent_id and self.student_id and not self.parent.students.filter(pk=self.student_id).exists():
            errors['parent'] = 'Parent must be linked to the student.'
        if self.assigned_teacher_id and self.section_id and not self.assigned_teacher.assigned_sections.filter(pk=self.section_id).exists():
            errors['assigned_teacher'] = 'Teacher must be assigned to this section.'
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return self.subject


class ParentQueryReply(TimeStampedModel):
    query = models.ForeignKey(
        ParentQuery,
        on_delete=models.CASCADE,
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
    )
    message = models.TextField()

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'Reply to {self.query}'
