from django.urls import path

from . import views

urlpatterns = [
    path('template/', views.template_download_view, name='analytics-template'),
]
