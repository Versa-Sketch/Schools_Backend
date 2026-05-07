from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('api/v1/', include('core.urls')),
    path('api/v1/notifications/', include('notifications.urls')),
    path('api/v1/principal/', include('principal.urls')),
    path('api/v1/teacher/', include('teacher.urls')),
    path('api/v1/student/', include('student.urls')),
    path('api/v1/parent/', include('parent.urls')),
    path('api/v1/analytics/', include('analytics.urls')),
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
