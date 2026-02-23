from datetime import timedelta

from django.db.models import Avg, Count, Q
from django.utils import timezone

from monitoring.models import AIMetric


def resolve_risk_level(critical_last_30min: int, suspicious_last_30min: int) -> str:
    if critical_last_30min >= 3:
        return "HIGH"
    if suspicious_last_30min >= 5:
        return "MEDIUM"
    return "LOW"


def get_session_analytics(session_id: int, as_of=None) -> dict:
    current_time = as_of or timezone.now()
    window_start = current_time - timedelta(minutes=30)

    session_metrics = AIMetric.objects.filter(session_id=session_id)
    recent_metrics = session_metrics.filter(created_at__gte=window_start)

    aggregates = session_metrics.aggregate(
        avg_productivity=Avg("productivity_score"),
        avg_anomaly=Avg("anomaly_score"),
        total_metrics=Count("id"),
        suspicious_count=Count("id", filter=Q(anomaly_label="suspicious")),
        critical_count=Count("id", filter=Q(anomaly_label="critical")),
    )

    suspicious_last_30min = recent_metrics.filter(anomaly_label="suspicious").count()
    critical_last_30min = recent_metrics.filter(anomaly_label="critical").count()
    anomaly_last_30min = recent_metrics.exclude(anomaly_label="normal").count()

    mature_count = 0
    for metric in session_metrics.only("features", "model_info"):
        model_info = metric.model_info or {}
        features = metric.features or {}
        mode = model_info.get("anomaly_mode")
        if mode == "statistical" or features.get("baseline_mature") is True:
            mature_count += 1

    total_metrics = aggregates["total_metrics"] or 0
    baseline_mature_ratio = (
        round(mature_count / total_metrics, 4) if total_metrics else 0.0
    )

    avg_productivity = aggregates["avg_productivity"]
    avg_anomaly = aggregates["avg_anomaly"]

    return {
        "avg_productivity": round(avg_productivity, 2) if avg_productivity is not None else 0.0,
        "avg_anomaly": round(avg_anomaly, 4) if avg_anomaly is not None else 0.0,
        "total_metrics": total_metrics,
        "suspicious_count": aggregates["suspicious_count"] or 0,
        "critical_count": aggregates["critical_count"] or 0,
        "anomaly_last_30min": anomaly_last_30min,
        "suspicious_last_30min": suspicious_last_30min,
        "critical_last_30min": critical_last_30min,
        "baseline_mature_ratio": baseline_mature_ratio,
        "risk_level": resolve_risk_level(
            critical_last_30min=critical_last_30min,
            suspicious_last_30min=suspicious_last_30min,
        ),
    }

