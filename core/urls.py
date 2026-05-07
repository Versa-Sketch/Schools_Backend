from django.urls import path

from . import views


urlpatterns = [
    path('auth/login/', views.login_view, name='auth-login'),
    path('auth/refresh/', views.refresh_token_view, name='auth-refresh'),
    path('auth/logout/', views.logout_view, name='auth-logout'),
    path('me/', views.current_user_view, name='current-user'),
    path('school/', views.school_view, name='school-detail'),
    path('classes/', views.class_list_view, name='class-list'),
    path('sections/', views.section_list_view, name='section-list'),
    path('subjects/', views.subject_list_view, name='subject-list'),
    path('calendar-events/', views.calendar_event_list_view, name='calendar-event-list'),
    path('announcements/', views.announcement_list_view, name='announcement-list'),
    path('announcements/<uuid:announcement_id>/', views.announcement_detail_view, name='announcement-detail'),
]
