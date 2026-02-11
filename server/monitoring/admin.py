from django.contrib import admin
from .models import AgentSession, ScreenshotLog


@admin.register(AgentSession)
class AgentSessionAdmin(admin.ModelAdmin):
    list_display = (
        "agent_name",
        "agent_version",
        "hostname",
        "username",
        "ip_address",
        "started_at",
    )
    search_fields = ("hostname", "username", "ip_address")


@admin.register(ScreenshotLog)
class ScreenshotLogAdmin(admin.ModelAdmin):
    list_display = ("session", "captured_at", "image_path")
    list_filter = ("captured_at",)
