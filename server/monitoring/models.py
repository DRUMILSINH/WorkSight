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

    image_path = models.CharField(max_length=500)
    captured_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Screenshot @ {self.captured_at}"

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

