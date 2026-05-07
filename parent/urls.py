from django.urls import path

from . import views

urlpatterns = [
    path('profile/pic/', views.profile_pic_view, name='parent-profile-pic'),
    path('profile/', views.profile_view, name='parent-profile'),
    path('students/', views.students_view, name='parent-students'),
    path('students/<uuid:student_id>/attendance/', views.student_attendance_view, name='parent-student-attendance'),
    path('students/<uuid:student_id>/announcements/', views.student_announcements_view, name='parent-student-announcements'),
    path('students/<uuid:student_id>/study-materials/', views.student_study_materials_view, name='parent-student-study-materials'),
    path('students/<uuid:student_id>/homework/', views.student_homework_view, name='parent-student-homework'),
    path('students/<uuid:student_id>/calendar-events/', views.student_calendar_view, name='parent-student-calendar'),
    path('students/<uuid:student_id>/results/', views.student_results_view, name='parent-student-results'),
    path('queries/', views.query_list_view, name='parent-queries'),
    path('queries/<uuid:query_id>/', views.query_detail_view, name='parent-query-detail'),
    path('queries/<uuid:query_id>/replies/', views.query_reply_view, name='parent-query-replies'),
]
