from django.contrib import admin
from .models import (
    AgentSession,
    ScreenshotLog,
    AgentHeartbeat,
    Recording,
    AgentToken,
    AIMetric,
)


@admin.register(AgentSession)
class AgentSessionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "agent_name",
        "agent_version",
        "hostname",
        "username",
        "ip_address",
        "started_at",
    )
    search_fields = ("hostname", "username", "ip_address")
    list_filter = ("agent_name", "started_at")
    date_hierarchy = "started_at"


@admin.register(ScreenshotLog)
class ScreenshotLogAdmin(admin.ModelAdmin):
    list_display = ("id", "session", "image", "captured_at")
    list_filter = ("captured_at",)
    search_fields = ("image",)
    date_hierarchy = "captured_at"


@admin.register(AgentHeartbeat)
class AgentHeartbeatAdmin(admin.ModelAdmin):
    list_display = ("session", "last_seen")


@admin.register(Recording)
class RecordingAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "session",
        "started_at",
        "ended_at",
        "drive_file_id",
    )
    list_filter = ("started_at",)
    search_fields = ("video_path", "drive_file_id")


@admin.register(AgentToken)
class AgentTokenAdmin(admin.ModelAdmin):
    list_display = ("session", "token")
    search_fields = ("token",)


@admin.register(AIMetric)
class AIMetricAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "session",
        "source_type",
        "productivity_score",
        "anomaly_score",
        "anomaly_label",
        "pipeline_status",
        "agent_timestamp",
    )
    list_filter = ("source_type", "anomaly_label", "pipeline_status", "feature_version")
    search_fields = ("source_ref", "idempotency_key", "error_code")
