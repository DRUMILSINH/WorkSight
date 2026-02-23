from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Dict, Any

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class AIMetricV1:
    agent_timestamp: str
    source_type: str
    source_ref: str
    feature_version: str
    features: dict[str, Any]
    productivity_score: float
    anomaly_score: float
    anomaly_label: str
    model_info: dict[str, Any]
    pipeline_status: str
    anomaly_explanation: Optional[Dict[str, Any]] = None
    anomaly_mode: Optional[str] = None
    anomaly_mode: str | None = None
    ocr_text_hash: str | None = None
    error_code: str | None = None
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_timestamp": self.agent_timestamp,
            "source_type": self.source_type,
            "source_ref": self.source_ref,
            "ocr_text_hash": self.ocr_text_hash,
            "feature_version": self.feature_version,
            "features": self.features,
            "productivity_score": self.productivity_score,
            "anomaly_score": self.anomaly_score,
            "anomaly_label": self.anomaly_label,
            "model_info": self.model_info,
            "pipeline_status": self.pipeline_status,
            "error_code": self.error_code,
            "error_message": self.error_message,
        }


@dataclass
class AIResultEnvelope:
    metric: AIMetricV1
    attempt: int = 0
    queued_at: str = field(default_factory=utc_now_iso)
    next_retry_at: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric": self.metric.to_dict(),
            "attempt": self.attempt,
            "queued_at": self.queued_at,
            "next_retry_at": self.next_retry_at,
        }
