from django.contrib import admin

from .models import StudentProfile


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'school', 'academic_class', 'section', 'roll_number', 'admission_number', 'is_active')
    list_filter = ('school', 'academic_class', 'section', 'is_active')
    search_fields = ('name', 'roll_number', 'admission_number', 'user__username')
