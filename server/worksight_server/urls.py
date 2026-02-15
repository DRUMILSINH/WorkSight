from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from monitoring.views import dashboard_home

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("monitoring.urls")),
    path('dashboard/', dashboard_home, name='dashboard_home'),
    path('', dashboard_home, name='home'),
]

# CRITICAL: This line allows you to see screenshots in the dashboard
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
