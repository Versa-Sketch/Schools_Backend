from django.urls import path

from . import views

urlpatterns = [
    path('template/', views.template_download_view, name='analytics-template'),
    path('upload/',   views.upload_view,             name='analytics-upload'),
    path('seed/',     views.seed_view,               name='analytics-seed'),
]
