import time
import socket
import threading
import hashlib
import random
from queue import Queue, Empty

from agent.api_client import BackendClient
from agent.logger import get_logger
from agent.system_info import collect_system_info
from agent.ai import AIResultEnvelope, AIQueueStore
from agent.config import (
    SCREENSHOT_INTERVAL_SECONDS,
    HEARTBEAT_INTERVAL_SECONDS,
    LOG_DIR,
    LOG_FILE_NAME,
    LOG_LEVEL,
    AGENT_NAME,
    AGENT_VERSION,
    AI_QUEUE_DB_PATH,
    AI_UPLOAD_BATCH_SIZE,
    AI_UPLOAD_POLL_SECONDS,
    AI_MAX_RETRIES,
    AI_BACKOFF_BASE_SECONDS,
    AI_MAX_QUEUE_BACKLOG,
    HEALTH_SNAPSHOT_INTERVAL_SECONDS,
)

from agent.services.screenshot_service import ScreenshotService
from agent.services.heartbeat_service import HeartbeatService
from agent.services.recording_service import RecordingService
from agent.services.ai_service import AIService


class WorkSightAgent:
    def __init__(self):
        self.logger = get_logger(LOG_DIR, LOG_FILE_NAME, LOG_LEVEL)

        self.hostname = socket.gethostname()
        self.system_info = collect_system_info()
        self.backend = BackendClient(self.logger)
        agent_id = self.system_info["hostname"]
        self.ai_service = AIService(self.logger, agent_id)
        self.ai_queue_store = AIQueueStore(AI_QUEUE_DB_PATH)
        self.capture_queue = Queue(maxsize=200)
        self.stop_event = threading.Event()
        self.worker_threads = []

        self.screenshot_service = ScreenshotService(self.backend, self.logger)
        self.heartbeat_service = HeartbeatService(self.backend)

        self.recording_service = RecordingService(
            backend=self.backend,
            logger=self.logger,
            hostname=self.hostname,
            stop_event=self.stop_event,
        )

    def start(self):
        self.logger.info(
            f"Agent started on {self.hostname}",
            extra={
                "metadata": {
                    "agent": AGENT_NAME,
                    "version": AGENT_VERSION,
                    "hostname": self.hostname,
                    **self.system_info,
                }
            },
        )

        # Register the session
        self.backend.create_session(self.system_info)
        self._start_workers()

        try:
            while True:
                time.sleep(1)
                if any(not worker.is_alive() for worker in self.worker_threads):
                    raise RuntimeError("A critical worker thread stopped unexpectedly")

        except KeyboardInterrupt:
            self.logger.info("Agent stopped by user")

        except Exception as e:
            self.logger.error(
                "Agent crashed",
                extra={"metadata": {"error": str(e)}},
            )
        finally:
            self.stop_event.set()
            for worker in self.worker_threads:
                worker.join(timeout=2)

    def _start_workers(self):
        self.worker_threads = [
            threading.Thread(target=self._heartbeat_loop, name="heartbeat-worker", daemon=True),
            threading.Thread(target=self._capture_loop, name="capture-worker", daemon=True),
            threading.Thread(target=self._ai_loop, name="ai-worker", daemon=True),
            threading.Thread(target=self._upload_loop, name="upload-worker", daemon=True),
            threading.Thread(target=self._health_loop, name="health-worker", daemon=True),
        ]
        for worker in self.worker_threads:
            worker.start()

    def _heartbeat_loop(self):
        while not self.stop_event.is_set():
            try:
                self.heartbeat_service.tick()
            except Exception as exc:
                self.logger.error(
                    "Heartbeat failed",
                    extra={"metadata": {"error": str(exc)}},
                )
            self.stop_event.wait(HEARTBEAT_INTERVAL_SECONDS)

    def _capture_loop(self):
        while not self.stop_event.is_set():
            try:
                item = self.screenshot_service.capture_and_send()
                self.recording_service.maybe_record()
                if item:
                    self.capture_queue.put(item, timeout=1)
            except Exception as exc:
                self.logger.error(
                    "Capture worker failed",
                    extra={"metadata": {"error": str(exc)}},
                )
            self.stop_event.wait(SCREENSHOT_INTERVAL_SECONDS)

    def _ai_loop(self):
        while not self.stop_event.is_set():
            try:
                item = self.capture_queue.get(timeout=1)
            except Empty:
                continue

            try:
                if self.ai_queue_store.backlog_count() >= AI_MAX_QUEUE_BACKLOG:
                    self.logger.warning(
                        "AI metric dropped due to backlog limit",
                        extra={"metadata": {"backlog": self.ai_queue_store.backlog_count()}},
                    )
                    continue

                metric = self.ai_service.process_screenshot(item["path"])
                envelope = AIResultEnvelope(metric=metric)
                idempotency_key = self._build_idempotency_key(metric)
                inserted = self.ai_queue_store.enqueue(envelope, idempotency_key)
                if inserted:
                    self.logger.info(
                        "AI metric queued",
                        extra={
                            "metadata": {
                                "source_ref": metric.source_ref,
                                "idempotency_key": idempotency_key,
                                "pipeline_status": metric.pipeline_status,
                            }
                        },
                    )
            except Exception as exc:
                self.logger.error(
                    "AI worker failed",
                    extra={"metadata": {"error": str(exc)}},
                )
            finally:
                self.capture_queue.task_done()

    def _upload_loop(self):
        while not self.stop_event.is_set():
            try:
                items = self.ai_queue_store.ready_items(AI_UPLOAD_BATCH_SIZE)
                for item in items:
                    self._upload_single(item)
            except Exception as exc:
                self.logger.error(
                    "Uploader worker failed",
                    extra={"metadata": {"error": str(exc)}},
                )
            self.stop_event.wait(AI_UPLOAD_POLL_SECONDS)

    def _health_loop(self):
        while not self.stop_event.is_set():
            try:
                self.logger.info(
                    "Agent health snapshot",
                    extra={
                        "metadata": {
                            "ai_worker_alive": self._is_worker_alive("ai-worker"),
                            "upload_worker_alive": self._is_worker_alive("upload-worker"),
                            "queue_backlog": self.ai_queue_store.backlog_count(),
                            "last_ai_upload_success_at": self.backend.last_ai_upload_success_at,
                        }
                    },
                )
            except Exception as exc:
                self.logger.error(
                    "Health worker failed",
                    extra={"metadata": {"error": str(exc)}},
                )
            self.stop_event.wait(HEALTH_SNAPSHOT_INTERVAL_SECONDS)

    def _upload_single(self, item: dict):
        row_id = item["id"]
        idempotency_key = item["idempotency_key"]
        payload = item["metric"]
        attempt = item["attempt"] + 1

        try:
            self.backend.log_ai_metric(payload, idempotency_key=idempotency_key)
            self.ai_queue_store.mark_success(row_id)
        except Exception as exc:
            if attempt >= AI_MAX_RETRIES:
                self.ai_queue_store.mark_dead_letter(row_id, str(exc))
                self.logger.error(
                    "AI metric moved to dead-letter queue",
                    extra={"metadata": {"error": str(exc), "idempotency_key": idempotency_key}},
                )
                return

            retry_delay = AI_BACKOFF_BASE_SECONDS * (2 ** (attempt - 1))
            retry_delay += random.uniform(0.0, 0.75)
            self.ai_queue_store.reschedule(
                row_id=row_id,
                attempt=attempt,
                next_retry_at=time.time() + retry_delay,
                error=str(exc),
            )

    def _build_idempotency_key(self, metric) -> str:
        timestamp_bucket = metric.agent_timestamp[:16]
        raw = f"{self.backend.session_id}:{metric.source_ref}:{metric.feature_version}:{timestamp_bucket}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _is_worker_alive(self, name: str) -> bool:
        for worker in self.worker_threads:
            if worker.name == name:
                return worker.is_alive()
        return False
