from django.contrib import admin

from .models import (
    AnalyticsExam,
    AnalyticsStudent,
    ExamResult,
    ExamSubject,
    QuestionAnalytics,
    QuestionResult,
    SectionAnalytics,
    StudentRisk,
)


@admin.register(AnalyticsExam)
class AnalyticsExamAdmin(admin.ModelAdmin):
    list_display = ['exam_name', 'exam_date', 'school', 'analytics_status', 'created_at']
    list_filter = ['analytics_status', 'school']
    search_fields = ['exam_name']


@admin.register(AnalyticsStudent)
class AnalyticsStudentAdmin(admin.ModelAdmin):
    list_display = ['name', 'student_ref_id', 'school', 'class_name', 'section_name']
    list_filter = ['school', 'class_name']
    search_fields = ['name', 'student_ref_id']


@admin.register(ExamSubject)
class ExamSubjectAdmin(admin.ModelAdmin):
    list_display = ['subject_name', 'exam', 'total_questions', 'max_marks']


@admin.register(ExamResult)
class ExamResultAdmin(admin.ModelAdmin):
    list_display = ['student', 'subject', 'total_marks', 'exam_rank', 'correct', 'wrong', 'unattempted']
    list_filter = ['subject__subject_name']


@admin.register(QuestionResult)
class QuestionResultAdmin(admin.ModelAdmin):
    list_display = ['student', 'subject', 'q_no', 'status']
    list_filter = ['status', 'subject__subject_name']


@admin.register(QuestionAnalytics)
class QuestionAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['q_no', 'subject', 'difficulty_tag', 'difficulty_index', 'has_key_error']
    list_filter = ['difficulty_tag', 'has_key_error', 'subject__subject_name']


@admin.register(SectionAnalytics)
class SectionAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['section', 'subject', 'avg_marks', 'median_marks', 'at_risk_count']


@admin.register(StudentRisk)
class StudentRiskAdmin(admin.ModelAdmin):
    list_display = ['student', 'subject', 'risk_label', 'performance_label', 'risk_score']
    list_filter = ['risk_label', 'performance_label']
