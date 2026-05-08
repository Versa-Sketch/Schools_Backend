from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    AbsentNotificationLog,
    AcademicCalendarEvent,
    AcademicClass,
    Announcement,
    AnnouncementAttachment,
    AnnouncementTarget,
    AttendanceSession,
    Homework,
    ParentQuery,
    ParentQueryReply,
    School,
    SchoolConfiguration,
    Section,
    StudentAttendance,
    StudentBulkUploadBatch,
    StudentBulkUploadRow,
    StudyMaterial,
    Subject,
    User,
)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('School Role', {'fields': ('role', 'phone_number', 'profile_pic')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('School Role', {'fields': ('role', 'phone_number')}),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff')
    list_filter = UserAdmin.list_filter + ('role',)


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ('name', 'subdomain', 'contact_phone', 'is_active')
    search_fields = ('name', 'subdomain', 'contact_phone')
    prepopulated_fields = {'subdomain': ('name',)}


@admin.register(SchoolConfiguration)
class SchoolConfigurationAdmin(admin.ModelAdmin):
    list_display = (
        'school',
        'attendance_frequency',
        'whatsapp_absent_automation_enabled',
        'parent_query_enabled',
    )
    list_filter = ('attendance_frequency', 'whatsapp_absent_automation_enabled', 'parent_query_enabled')


@admin.register(AcademicClass)
class AcademicClassAdmin(admin.ModelAdmin):
    list_display = ('name', 'school', 'display_order')
    list_filter = ('school',)
    search_fields = ('name', 'school__name')


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'academic_class', 'school', 'class_teacher')
    list_filter = ('school', 'academic_class')
    search_fields = ('name', 'academic_class__name', 'school__name')


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'school', 'is_active')
    list_filter = ('school', 'is_active')
    search_fields = ('name', 'code')


@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):
    list_display = ('section', 'school', 'date', 'slot', 'taken_by', 'confirmed_at')
    list_filter = ('school', 'date', 'slot')
    search_fields = ('section__name', 'taken_by__name')


@admin.register(StudentAttendance)
class StudentAttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'session', 'status')
    list_filter = ('status', 'session__school', 'session__date')
    search_fields = ('student__name',)


@admin.register(AbsentNotificationLog)
class AbsentNotificationLogAdmin(admin.ModelAdmin):
    list_display = ('attendance', 'parent', 'channel', 'status', 'sent_at')
    list_filter = ('channel', 'status')


class AnnouncementTargetInline(admin.TabularInline):
    model = AnnouncementTarget
    extra = 0


class AnnouncementAttachmentInline(admin.TabularInline):
    model = AnnouncementAttachment
    extra = 0


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'school', 'author_role', 'audience', 'published_at', 'is_active')
    list_filter = ('school', 'author_role', 'audience', 'is_active')
    search_fields = ('title', 'body')
    inlines = (AnnouncementTargetInline, AnnouncementAttachmentInline)


@admin.register(AnnouncementTarget)
class AnnouncementTargetAdmin(admin.ModelAdmin):
    list_display = ('announcement', 'academic_class', 'section')


@admin.register(AnnouncementAttachment)
class AnnouncementAttachmentAdmin(admin.ModelAdmin):
    list_display = ('announcement', 'filename', 'content_type')


@admin.register(StudyMaterial)
class StudyMaterialAdmin(admin.ModelAdmin):
    list_display = ('title', 'school', 'section', 'subject', 'uploaded_by', 'material_date')
    list_filter = ('school', 'section', 'subject', 'material_date')
    search_fields = ('title', 'description')


@admin.register(Homework)
class HomeworkAdmin(admin.ModelAdmin):
    list_display = ('section', 'subject', 'assigned_by', 'deadline')
    list_filter = ('school', 'section', 'subject', 'deadline')


@admin.register(StudentBulkUploadBatch)
class StudentBulkUploadBatchAdmin(admin.ModelAdmin):
    list_display = ('school', 'uploaded_by', 'status', 'total_rows', 'success_count', 'error_count')
    list_filter = ('school', 'status')


@admin.register(StudentBulkUploadRow)
class StudentBulkUploadRowAdmin(admin.ModelAdmin):
    list_display = ('batch', 'row_number', 'status', 'created_student', 'created_parent')
    list_filter = ('status',)


@admin.register(AcademicCalendarEvent)
class AcademicCalendarEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'school', 'event_type', 'start_date', 'end_date')
    list_filter = ('school', 'event_type', 'start_date')
    search_fields = ('title', 'description')


@admin.register(ParentQuery)
class ParentQueryAdmin(admin.ModelAdmin):
    list_display = ('subject', 'school', 'parent', 'student', 'assigned_teacher', 'status')
    list_filter = ('school', 'status')
    search_fields = ('subject', 'message', 'parent__name', 'student__name')


@admin.register(ParentQueryReply)
class ParentQueryReplyAdmin(admin.ModelAdmin):
    list_display = ('query', 'sender', 'created_at')
