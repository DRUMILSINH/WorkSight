from django.urls import path
from . import views

urlpatterns = [
    path("sessions/", views.create_session),
    path("screenshots/", views.log_screenshot),

    # Session-scoped endpoints
    path("sessions/<int:session_id>/heartbeat/", views.heartbeat),
    path("sessions/<int:session_id>/recordings/", views.upload_recording),

    path("dashboard/", views.dashboard),
]
