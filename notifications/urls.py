from django.urls import path

from . import views

urlpatterns = [
    path('', views.notification_list_view, name='notification-list'),
    path('read/', views.mark_read_view, name='notification-mark-read'),
    path('unread-count/', views.unread_count_view, name='notification-unread-count'),
]
