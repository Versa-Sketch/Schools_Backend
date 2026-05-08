from django.urls import path

from . import views

urlpatterns = [
    path('template/',  views.template_download_view, name='analytics-template'),
    path('upload/',    views.upload_view,            name='analytics-upload'),
    path('seed/',      views.seed_view,              name='analytics-seed'),
    path('exams/',     views.exams_list_view,        name='analytics-exams-list'),

    # 7a — Principal screens
    path('dashboard/', views.dashboard_view,         name='analytics-dashboard'),
    path('class/<uuid:class_id>/', views.class_detail_view, name='analytics-class-detail'),

    # 7b — Section screens (Principal + Teacher/own section)
    path('section/<uuid:section_id>/',
         views.section_students_view, name='analytics-section-students'),
    path('section/<uuid:section_id>/subject/<str:subject_name>/heatmap/',
         views.question_heatmap_view, name='analytics-question-heatmap'),
    path('section/<uuid:section_id>/subject/<str:subject_name>/question/<int:q_no>/',
         views.question_detail_view,  name='analytics-question-detail'),

    # 7c — Student screens (Principal, Teacher/own section, Student/own, Parent/own child)
    path('student/<uuid:student_id>/',
         views.student_summary_view, name='analytics-student-summary'),
    path('student/<uuid:student_id>/subject/<str:subject_name>/',
         views.student_subject_view, name='analytics-student-subject'),
]
