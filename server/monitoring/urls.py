from django.urls import path
from . import views

urlpatterns = [
    path("sessions/", views.create_session),
    path("screenshots/", views.log_screenshot),
]
