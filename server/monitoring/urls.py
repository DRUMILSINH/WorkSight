from django.urls import path
from . import views
from .views import dashboard_home

urlpatterns = [
    path("sessions/", views.create_session),
    path("screenshots/", views.log_screenshot),

    # Session-scoped endpoints
    path("sessions/<int:session_id>/heartbeat/", views.heartbeat),
    path("sessions/<int:session_id>/recordings/", views.upload_recording),
    path("sessions/<int:session_id>/ai-metrics/", views.create_ai_metric),

    path('dashboard/', dashboard_home, name='dashboard_home'),
    path('', dashboard_home, name='home'),
]
