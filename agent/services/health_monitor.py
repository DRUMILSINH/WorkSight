import shutil
from datetime import datetime


class HealthMonitor:
    def __init__(self, backend, hostname, logger):
        self.backend = backend
        self.hostname = hostname
        self.logger = logger

    def update(self):
        try:
            total, used, free = shutil.disk_usage("/")

            disk_percent = (used / total) * 100
            free_gb = free / (1024 ** 3)

            stats = self.backend.get_recording_stats(self.hostname)

            self.backend.update_system_health({
                "hostname": self.hostname,
                "last_recording_time": stats.get("last_recording_time"),
                "last_upload_time": stats.get("last_upload_time"),
                "total_recordings": stats.get("total_recordings"),
                "total_failures": stats.get("total_failures"),
                "disk_usage_percent": disk_percent,
                "free_disk_gb": free_gb,
                "last_error": stats.get("last_error"),
            })

        except Exception as e:
            self.logger.error(
                "Health monitor update failed",
                extra={"metadata": {"error": str(e)}},
            )
