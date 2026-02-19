import hashlib
import re
import time
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

from agent.ai.types import AIMetricV1
from agent.config import (
    AI_FEATURE_VERSION,
    AI_MODEL_NAME,
    AI_MODEL_VERSION,
    AI_PIPELINE_TIMEOUT_SECONDS,
)

try:
    import pytesseract
except Exception:
    pytesseract = None


class AIService:
    def __init__(self, logger):
        self.logger = logger

    def process_screenshot(self, image_path: str) -> AIMetricV1:
        started = time.perf_counter()
        now_iso = datetime.now(timezone.utc).isoformat()
        source_ref = str(Path(image_path).resolve())

        pipeline_status = "ok"
        error_code = None
        error_message = None
        raw_text = ""

        try:
            if pytesseract is not None:
                raw_text = pytesseract.image_to_string(Image.open(image_path))
            else:
                pipeline_status = "partial"
                error_code = "OCR_UNAVAILABLE"
                error_message = "pytesseract is not installed"

            elapsed = time.perf_counter() - started
            if elapsed > AI_PIPELINE_TIMEOUT_SECONDS:
                pipeline_status = "partial"
                error_code = "PIPELINE_TIMEOUT"
                error_message = f"pipeline exceeded {AI_PIPELINE_TIMEOUT_SECONDS}s"

            redacted = self._redact_text(raw_text)
            features = self._extract_features(redacted)
            productivity = self._productivity_score(redacted, features)
            anomaly = self._anomaly_score(features)
            label = self._anomaly_label(anomaly)
            ocr_hash = hashlib.sha256(redacted.encode("utf-8")).hexdigest() if redacted else None

            return AIMetricV1(
                agent_timestamp=now_iso,
                source_type="screenshot",
                source_ref=source_ref,
                ocr_text_hash=ocr_hash,
                feature_version=AI_FEATURE_VERSION,
                features=features,
                productivity_score=productivity,
                anomaly_score=anomaly,
                anomaly_label=label,
                model_info={
                    "name": AI_MODEL_NAME,
                    "version": AI_MODEL_VERSION,
                    "latency_ms": round((time.perf_counter() - started) * 1000, 2),
                },
                pipeline_status=pipeline_status,
                error_code=error_code,
                error_message=error_message,
            )
        except Exception as exc:
            self.logger.error(
                "AI pipeline failed",
                extra={"metadata": {"error": str(exc), "source_ref": source_ref}},
            )
            return AIMetricV1(
                agent_timestamp=now_iso,
                source_type="screenshot",
                source_ref=source_ref,
                ocr_text_hash=None,
                feature_version=AI_FEATURE_VERSION,
                features={"word_count": 0, "line_count": 0, "focus_keyword_hits": 0},
                productivity_score=0.0,
                anomaly_score=1.0,
                anomaly_label="critical",
                model_info={
                    "name": AI_MODEL_NAME,
                    "version": AI_MODEL_VERSION,
                    "latency_ms": round((time.perf_counter() - started) * 1000, 2),
                },
                pipeline_status="failed",
                error_code="PIPELINE_ERROR",
                error_message=str(exc),
            )

    def _redact_text(self, text: str) -> str:
        redacted = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[EMAIL]", text)
        redacted = re.sub(r"\b\d{3,}\b", "[NUMBER]", redacted)
        return redacted.strip()

    def _extract_features(self, text: str) -> dict:
        words = re.findall(r"\w+", text.lower())
        lines = [line for line in text.splitlines() if line.strip()]
        focus_terms = {"jira", "ticket", "design", "spec", "review", "code", "build", "deploy"}
        distract_terms = {"youtube", "netflix", "tiktok", "game", "shopping"}

        focus_hits = sum(1 for token in words if token in focus_terms)
        distract_hits = sum(1 for token in words if token in distract_terms)
        alpha_chars = sum(1 for ch in text if ch.isalpha())
        total_chars = len(text) if text else 1

        return {
            "word_count": len(words),
            "line_count": len(lines),
            "focus_keyword_hits": focus_hits,
            "distraction_keyword_hits": distract_hits,
            "alpha_ratio": round(alpha_chars / total_chars, 4),
        }

    def _productivity_score(self, text: str, features: dict) -> float:
        base = 50.0
        base += min(features["focus_keyword_hits"] * 6.0, 30.0)
        base -= min(features["distraction_keyword_hits"] * 10.0, 40.0)
        if features["word_count"] < 3:
            base -= 10.0
        if not text:
            base -= 15.0
        return round(max(0.0, min(100.0, base)), 2)

    def _anomaly_score(self, features: dict) -> float:
        score = 0.1
        if features["word_count"] < 2:
            score += 0.4
        if features["alpha_ratio"] < 0.2:
            score += 0.3
        if features["distraction_keyword_hits"] > 1:
            score += 0.3
        return round(max(0.0, min(1.0, score)), 3)

    def _anomaly_label(self, anomaly_score: float) -> str:
        if anomaly_score >= 0.75:
            return "critical"
        if anomaly_score >= 0.4:
            return "suspicious"
        return "normal"
