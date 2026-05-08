from django.urls import path

from . import views

urlpatterns = [
    path('template/',  views.template_download_view, name='analytics-template'),
    path('upload/',    views.upload_view,            name='analytics-upload'),
    path('seed/',      views.seed_view,              name='analytics-seed'),
    path('exams/',     views.exams_list_view,        name='analytics-exams-list'),
    path('dashboard/', views.dashboard_view,         name='analytics-dashboard'),
    path('class/<str:class_name>/', views.class_detail_view, name='analytics-class-detail'),

    # Section screens (7b)
    path('section/<uuid:section_id>/',
         views.section_students_view, name='analytics-section-students'),
    path('section/<uuid:section_id>/subject/<str:subject_name>/heatmap/',
         views.question_heatmap_view, name='analytics-question-heatmap'),
    path('section/<uuid:section_id>/subject/<str:subject_name>/question/<int:q_no>/',
         views.question_detail_view,  name='analytics-question-detail'),
]
