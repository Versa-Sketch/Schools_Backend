from django.urls import path

from . import views

urlpatterns = [
    path('configuration/', views.configuration_view, name='principal-configuration'),
    path('teachers/', views.teacher_list_view, name='principal-teacher-list'),
    path('teachers/<uuid:teacher_id>/', views.teacher_detail_view, name='principal-teacher-detail'),
    path('students/bulk-upload/', views.bulk_upload_view, name='principal-bulk-upload'),
    path('students/bulk-upload/<uuid:batch_id>/', views.bulk_upload_status_view, name='principal-bulk-upload-status'),
    path('announcements/', views.announcement_create_view, name='principal-announcement-create'),
    path('calendar-events/', views.calendar_event_create_view, name='principal-calendar-event-create'),
    path('sections/', views.section_list_view, name='principal-section-list'),
    path('sections/<uuid:section_id>/', views.section_detail_view, name='principal-section-detail'),
    path('attendance/daily-summary/', views.daily_attendance_summary_view, name='principal-attendance-daily-summary'),
    path('attendance/classes/<uuid:class_id>/', views.class_attendance_detail_view, name='principal-attendance-class-detail'),
]
