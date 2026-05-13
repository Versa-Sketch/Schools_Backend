from django.urls import path

from . import views

urlpatterns = [
    path('template/', views.template_download_view, name='analytics-template'),
    path('seed/', views.seed_view, name='analytics-seed'),

    # Exam management (GET=list, POST=create)
    path('exams/', views.exams_view, name='analytics-exams'),
    path('exams/<uuid:exam_id>/upload/', views.upload_exam_view, name='analytics-exams-upload'),
    path('exams/<uuid:exam_id>/overview/', views.exam_overview_view, name='analytics-exams-overview'),

    # Class-level subject drill-down
    path('exams/<uuid:exam_id>/subjects/<uuid:subject_id>/questions/',
         views.class_subject_questions_view, name='analytics-class-subject-questions'),
    path('exams/<uuid:exam_id>/subjects/<uuid:subject_id>/questions/<int:q_no>/students/',
         views.class_question_students_view, name='analytics-class-question-students'),

    # Section-level drill-down
    path('exams/<uuid:exam_id>/sections/<uuid:section_id>/',
         views.section_detail_view, name='analytics-section-detail'),
    path('exams/<uuid:exam_id>/sections/<uuid:section_id>/subjects/<uuid:subject_id>/questions/',
         views.section_subject_questions_view, name='analytics-section-subject-questions'),
    path('exams/<uuid:exam_id>/sections/<uuid:section_id>/subjects/<uuid:subject_id>/questions/<int:q_no>/students/',
         views.section_question_students_view, name='analytics-section-question-students'),


    # Student screens (principal/teacher/student/parent access)
    path('student/<uuid:student_id>/exams/', views.student_all_exams_view, name='analytics-student-all-exams'),
    path('student/<uuid:student_id>/', views.student_summary_view, name='analytics-student-summary'),
    path('student/<uuid:student_id>/subject/<uuid:subject_id>/',
         views.student_subject_view, name='analytics-student-subject'),

    # Legacy routes kept for backward compatibility
    path('upload/', views.upload_view, name='analytics-upload'),
    path('dashboard/', views.dashboard_view, name='analytics-dashboard'),
    path('class/<uuid:class_id>/', views.class_detail_view, name='analytics-class-detail'),
    path('section/<uuid:section_id>/', views.section_students_view, name='analytics-section-students'),
    path('section/<uuid:section_id>/subject/<uuid:subject_id>/heatmap/',
         views.question_heatmap_view, name='analytics-question-heatmap'),
    path('section/<uuid:section_id>/subject/<uuid:subject_id>/question/<int:q_no>/',
         views.question_detail_view, name='analytics-question-detail'),
]
