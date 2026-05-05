from django.contrib import admin

from .models import TeacherProfile


@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'school', 'mobile_number', 'primary_subject')
    list_filter = ('school', 'primary_subject')
    search_fields = ('name', 'mobile_number', 'user__username')
    filter_horizontal = ('assigned_sections',)
