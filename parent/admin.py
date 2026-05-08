from django.contrib import admin

from .models import ParentProfile


@admin.register(ParentProfile)
class ParentProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'school', 'phone_number')
    list_filter = ('school',)
    search_fields = ('name', 'user__phone_number', 'user__username')
    filter_horizontal = ('students',)

    def phone_number(self, obj):
        return obj.user.phone_number
    phone_number.short_description = 'Phone Number'
