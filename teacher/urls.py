from django.urls import path

from . import views

urlpatterns = [
    path('profile/pic/', views.profile_pic_view, name='teacher-profile-pic'),
    path('sections/', views.sections_view, name='teacher-sections'),
    path('sections/<uuid:section_id>/students/', views.section_students_view, name='teacher-section-students'),
    path('attendance-sessions/', views.attendance_session_create_view, name='teacher-attendance-sessions'),
    path('attendance-sessions/<uuid:session_id>/students/', views.attendance_students_view, name='teacher-attendance-students'),
    path('attendance-sessions/<uuid:session_id>/confirm/', views.attendance_confirm_view, name='teacher-attendance-confirm'),
    path('announcements/', views.announcement_create_view, name='teacher-announcements'),
    path('study-materials/', views.study_material_view, name='teacher-study-materials'),
    path('homework/', views.homework_view, name='teacher-homework'),
    path('parent-queries/', views.parent_query_list_view, name='teacher-parent-queries'),
    path('parent-queries/<uuid:query_id>/replies/', views.parent_query_reply_view, name='teacher-parent-query-replies'),
    path('parent-queries/<uuid:query_id>/close/', views.parent_query_close_view, name='teacher-parent-query-close'),
    path('exams/<uuid:exam_id>/marks/', views.exam_marks_view, name='teacher-exam-marks'),
]
