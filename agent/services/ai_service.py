import hashlib
import time
from datetime import datetime, timezone
from pathlib import Path

from agent.ai.types import AIMetricV1
from agent.ai.extractors.ocr_extractor import OCRExtractor
from agent.ai.feature_engineering.text_features import TextFeatureEngineer
from agent.ai.models.productivity_model import ProductivityModel
from agent.ai.models.anomaly_model import AnomalyModel
from agent.ai.baseline_store import BaselineStore
from agent.config import (
    AI_FEATURE_VERSION,
    AI_MODEL_NAME,
    AI_MODEL_VERSION,
    AI_PIPELINE_TIMEOUT_SECONDS,
)


class AIService:
    """
    AI Pipeline Orchestrator.

    Responsibilities:
    - Run OCR
    - Extract features
    - Score productivity
    - Score anomaly (statistical + fallback)
    - Update per-agent baseline
    - Return AIMetricV1
    
    Does NOT contain:
    - Statistical math
    - Baseline calculations
    - ML logic
    """

    def __init__(self, logger, agent_id: str):
        self.logger = logger

        # Core pipeline modules
        self.extractor = OCRExtractor()
        self.feature_engineer = TextFeatureEngineer()
        self.productivity_model = ProductivityModel()

        # Per-agent baseline
        baseline_dir = Path("agent/ai/baselines")
        baseline_dir.mkdir(parents=True, exist_ok=True)
        baseline_path = baseline_dir / f"{agent_id}.json"

        self.baseline = BaselineStore(str(baseline_path))

        # Inject baseline into anomaly model
        self.anomaly_model = AnomalyModel(self.baseline)
        self._baseline_mature_logged = False

    # ---------------------------------------------------------

    def process_screenshot(self, image_path: str) -> AIMetricV1:
        started = time.perf_counter()
        now_iso = datetime.now(timezone.utc).isoformat()
        source_ref = str(Path(image_path).resolve())

        pipeline_status = "ok"
        error_code = None
        error_message = None

        try:
            # -------------------------------------------------
            # 1️⃣ OCR
            # -------------------------------------------------
            raw_text, err_code, err_msg = self.extractor.extract_text(image_path)

            if err_code:
                pipeline_status = "partial"
                error_code = err_code
                error_message = err_msg

            # -------------------------------------------------
            # 2️⃣ Timeout Guard
            # -------------------------------------------------
            if (time.perf_counter() - started) > AI_PIPELINE_TIMEOUT_SECONDS:
                pipeline_status = "partial"
                error_code = "PIPELINE_TIMEOUT"
                error_message = (
                    f"pipeline exceeded {AI_PIPELINE_TIMEOUT_SECONDS}s"
                )

            # -------------------------------------------------
            # 3️⃣ Redaction + Feature Engineering
            # -------------------------------------------------
            redacted = self.feature_engineer.redact(raw_text)
            features = self.feature_engineer.extract(redacted)

            # -------------------------------------------------
            # 4️⃣ Productivity Scoring
            # -------------------------------------------------
            productivity = self.productivity_model.predict(
                redacted,
                features,
            )

            # -------------------------------------------------
            # 5️⃣ Anomaly Scoring (uses baseline)
            # IMPORTANT: Score BEFORE updating baseline
            # -------------------------------------------------
            anomaly_score, explanation = self.anomaly_model.evaluate(features)
            anomaly_label = self.anomaly_model.label(anomaly_score)
            anomaly_mode = explanation.get("mode")


            # -------------------------------------------------
            # 6️⃣ Update Baseline AFTER scoring
            # -------------------------------------------------
            self.baseline.update(features)

            # -------------------------------------------------
            # Baseline maturity tracking (log once)
            # -------------------------------------------------
            if (
                not self._baseline_mature_logged
                and self.anomaly_model._baseline_ready()
            ):
                self.logger.info(
                    "Baseline matured — switching to statistical anomaly mode.",
                    extra={
                        "metadata": {
                            "source": "ai_service",
                        }
                    },
                )
                self._baseline_mature_logged = True

            # -------------------------------------------------
            # 7️⃣ Hash OCR Text
            # -------------------------------------------------
            ocr_hash = (
                hashlib.sha256(redacted.encode("utf-8")).hexdigest()
                if redacted
                else None
            )

            # -------------------------------------------------
            # 8️⃣ Build Metric DTO
            # -------------------------------------------------
            return AIMetricV1(
                agent_timestamp=now_iso,
                source_type="screenshot",
                source_ref=source_ref,
                ocr_text_hash=ocr_hash,
                feature_version=AI_FEATURE_VERSION,
                features=features,
                productivity_score=productivity,
                anomaly_score=anomaly_score,
                anomaly_label=anomaly_label,
                anomaly_mode=anomaly_mode,
                anomaly_explanation=explanation,
                model_info={
                    "name": AI_MODEL_NAME,
                    "version": AI_MODEL_VERSION,
                    "latency_ms": round(
                        (time.perf_counter() - started) * 1000,
                        2,
                    ),
                },
                pipeline_status=pipeline_status,
                error_code=error_code,
                error_message=error_message,
            )

        except Exception as exc:
            # Structured logging
            self.logger.error(
                "AI pipeline failed",
                extra={
                    "metadata": {
                        "error": str(exc),
                        "source_ref": source_ref,
                    }
                },
            )

            # Safe fallback metric (never crash agent)
            return AIMetricV1(
                agent_timestamp=now_iso,
                source_type="screenshot",
                source_ref=source_ref,
                ocr_text_hash=None,
                feature_version=AI_FEATURE_VERSION,
                features={},
                productivity_score=0.0,
                anomaly_score=1.0,
                anomaly_label="critical",
                model_info={
                    "name": AI_MODEL_NAME,
                    "version": AI_MODEL_VERSION,
                    "latency_ms": round(
                        (time.perf_counter() - started) * 1000,
                        2,
                    ),
                },
                pipeline_status="failed",
                error_code="PIPELINE_ERROR",
                error_message=str(exc),
            )
