from django.urls import path

from . import views

urlpatterns = [
    path('profile/pic/', views.profile_pic_view, name='student-profile-pic'),
    path('profile/', views.profile_view, name='student-profile'),
    path('attendance/', views.attendance_view, name='student-attendance'),
    path('announcements/', views.announcements_view, name='student-announcements'),
    path('study-materials/', views.study_materials_view, name='student-study-materials'),
    path('homework/', views.homework_view, name='student-homework'),
    path('calendar-events/', views.calendar_events_view, name='student-calendar-events'),
    path('exams/', views.exams_view, name='student-exams'),
    path('exams/<uuid:exam_id>/subjects/', views.exam_subjects_view, name='student-exam-subjects'),
    path('exams/<uuid:exam_id>/subjects/<uuid:subject_id>/questions/',
         views.exam_subject_questions_view, name='student-exam-subject-questions'),
]
