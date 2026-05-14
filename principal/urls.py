from django.urls import path

from . import views

from analytics import views as analytics_views

urlpatterns = [
    path('configuration/', views.configuration_view, name='principal-configuration'),
    path('teachers/', views.teacher_list_view, name='principal-teacher-list'),
    path('teachers/<uuid:teacher_id>/', views.teacher_detail_view, name='principal-teacher-detail'),
    path('students/bulk-upload/', views.bulk_upload_view, name='principal-bulk-upload'),
    path('students/bulk-upload/<uuid:batch_id>/', views.bulk_upload_status_view, name='principal-bulk-upload-status'),
    path('teachers/bulk-upload/', views.teacher_bulk_upload_view, name='principal-teacher-bulk-upload'),
    path('teachers/bulk-upload/<uuid:batch_id>/', views.teacher_bulk_upload_status_view, name='principal-teacher-bulk-upload-status'),
    path('announcements/', views.announcement_create_view, name='principal-announcement-create'),
    path('calendar-events/', views.calendar_event_create_view, name='principal-calendar-event-create'),
    path('calendar-events/<uuid:event_id>/', views.calendar_event_detail_view, name='principal-calendar-event-detail'),
    path('sections/', views.section_list_view, name='principal-section-list'),
    path('sections/<uuid:section_id>/', views.section_detail_view, name='principal-section-detail'),
    path('classes/', views.classes_view, name='principal-classes'),
    path('classes/<uuid:class_id>/', views.class_detail_view, name='principal-class-detail'),
    path('exams/', analytics_views.exams_view, name='principal-exams'),
    path('analytics/', analytics_views.dashboard_view, name='principal-analytics'),
    path('subjects/', views.subject_create_view, name='principal-subject-create'),
    path('subjects/<uuid:subject_id>/', views.subject_detail_view, name='principal-subject-detail'),
    path('attendance/daily-summary/', views.daily_attendance_summary_view, name='principal-attendance-daily-summary'),
    path('attendance/classes/<uuid:class_id>/', views.class_attendance_detail_view, name='principal-attendance-class-detail'),
]
