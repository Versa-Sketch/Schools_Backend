from django.contrib import admin

from .models import AdminProfile, PrincipalProfile


@admin.register(PrincipalProfile)
class PrincipalProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'school', 'phone_number')
    list_filter = ('school',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'user__phone_number')

    def phone_number(self, obj):
        return obj.user.phone_number
    phone_number.short_description = 'Phone Number'


@admin.register(AdminProfile)
class AdminProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'school', 'phone_number')
    list_filter = ('school',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'user__phone_number')

    def phone_number(self, obj):
        return obj.user.phone_number
    phone_number.short_description = 'Phone Number'
