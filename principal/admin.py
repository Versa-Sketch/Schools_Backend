from django.contrib import admin

from .models import AdminProfile, PrincipalProfile


@admin.register(PrincipalProfile)
class PrincipalProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'school', 'mobile_number')
    list_filter = ('school',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'mobile_number')


@admin.register(AdminProfile)
class AdminProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'school', 'mobile_number')
    list_filter = ('school',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'mobile_number')
