from django.urls import path

from . import views


urlpatterns = [
    path('auth/login/', views.login_view, name='auth-login'),
    path('auth/refresh/', views.refresh_token_view, name='auth-refresh'),
    path('auth/logout/', views.logout_view, name='auth-logout'),
    path('me/', views.current_user_view, name='current-user'),
]
