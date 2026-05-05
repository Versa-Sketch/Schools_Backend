from django.contrib import admin

from .models import ParentProfile


@admin.register(ParentProfile)
class ParentProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'school', 'mobile_number')
    list_filter = ('school',)
    search_fields = ('name', 'mobile_number', 'user__username')
    filter_horizontal = ('students',)
