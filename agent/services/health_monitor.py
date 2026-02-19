import shutil


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

            snapshot = {
                "hostname": self.hostname,
                "disk_usage_percent": disk_percent,
                "free_disk_gb": free_gb,
            }

            if hasattr(self.backend, "update_system_health"):
                self.backend.update_system_health(snapshot)
            else:
                self.logger.info(
                    "Health snapshot",
                    extra={"metadata": snapshot},
                )

        except Exception as e:
            self.logger.error(
                "Health monitor update failed",
                extra={"metadata": {"error": str(e)}},
            )
