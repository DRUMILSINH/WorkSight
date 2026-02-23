from django.db import models


class AgentSession(models.Model):
    agent_name = models.CharField(max_length=100)
    agent_version = models.CharField(max_length=20)

    hostname = models.CharField(max_length=255)
    username = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField()

    started_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.agent_name} @ {self.hostname} ({self.started_at})"


class ScreenshotLog(models.Model):
    session = models.ForeignKey(
        AgentSession,
        on_delete=models.CASCADE,
        related_name="screenshots"
    )

    image = models.ImageField(upload_to="screenshots/", blank=True, null=True)
    captured_at = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Screenshot {self.id} @ {self.captured_at}"

class AgentHeartbeat(models.Model):
    session = models.OneToOneField(
        AgentSession,
        on_delete=models.CASCADE,
        related_name="heartbeat"
    )
    last_seen = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Heartbeat @ {self.last_seen}"

class Recording(models.Model):

    STATUS_CHOICES = [
        ('CREATED', 'Created'),
        ('RECORDED', 'Recorded'),
        ('UPLOADING', 'Uploading'),
        ('UPLOADED', 'Uploaded'),
        ('FAILED', 'Failed'),
    ]

    session = models.ForeignKey(
        AgentSession,
        on_delete=models.CASCADE,
        related_name="recordings"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='CREATED'
    )

    video_path = models.CharField(max_length=512)
    drive_file_id = models.CharField(max_length=256, blank=True, null=True)

    retry_count = models.IntegerField(default=0)
    error_message = models.TextField(blank=True, null=True)

    file_size_bytes = models.BigIntegerField(null=True, blank=True)

    started_at = models.DateTimeField()
    ended_at = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    ai_processed = models.BooleanField(default=False)

    def __str__(self):
        return f"Recording {self.id} - {self.status}"
    
class AgentToken(models.Model):
    session = models.OneToOneField(
        AgentSession,
        on_delete=models.CASCADE,
        related_name="token"
    )
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)


class AIMetric(models.Model):
    SOURCE_TYPE_CHOICES = [
        ("screenshot", "Screenshot"),
        ("recording_window", "Recording Window"),
    ]

    ANOMALY_LABEL_CHOICES = [
        ("normal", "Normal"),
        ("suspicious", "Suspicious"),
        ("critical", "Critical"),
    ]

    PIPELINE_STATUS_CHOICES = [
        ("ok", "OK"),
        ("partial", "Partial"),
        ("failed", "Failed"),
    ]

    session = models.ForeignKey(
        AgentSession,
        on_delete=models.CASCADE,
        related_name="ai_metrics",
    )
    source_type = models.CharField(max_length=32, choices=SOURCE_TYPE_CHOICES)
    source_ref = models.CharField(max_length=1024)
    ocr_text_hash = models.CharField(max_length=64, blank=True, null=True)
    feature_version = models.CharField(max_length=64)
    features = models.JSONField(default=dict)
    productivity_score = models.FloatField()
    anomaly_score = models.FloatField()
    anomaly_label = models.CharField(max_length=32, choices=ANOMALY_LABEL_CHOICES)
    model_info = models.JSONField(default=dict)
    pipeline_status = models.CharField(max_length=32, choices=PIPELINE_STATUS_CHOICES)
    error_code = models.CharField(max_length=64, blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    idempotency_key = models.CharField(max_length=64, unique=True)
    agent_timestamp = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["session", "created_at"]),
            models.Index(fields=["anomaly_label"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"AI Metric {self.id} ({self.anomaly_label})"

