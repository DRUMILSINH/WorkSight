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
    captured_at = models.DateTimeField()

    def __str__(self):
        return f"Screenshot @ {self.captured_at}"
