from django.contrib import admin

from .models import TeacherProfile


@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'school', 'phone_number', 'primary_subject')
    list_filter = ('school', 'primary_subject')
    search_fields = ('name', 'user__phone_number', 'user__username')
    filter_horizontal = ('assigned_sections',)

    def phone_number(self, obj):
        return obj.user.phone_number
    phone_number.short_description = 'Phone Number'
