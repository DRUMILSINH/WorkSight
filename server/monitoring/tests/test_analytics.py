from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from monitoring.models import AIMetric, AgentSession
from monitoring.services.analytics import get_session_analytics, resolve_risk_level


class SessionAnalyticsTests(TestCase):
    def setUp(self):
        self.session = AgentSession.objects.create(
            agent_name="agent-x",
            agent_version="1.0.0",
            hostname="host-1",
            username="user-1",
            ip_address="127.0.0.1",
        )

    def _create_metric(
        self,
        *,
        label="normal",
        productivity=50.0,
        anomaly=0.2,
        created_at=None,
        model_info=None,
        features=None,
        suffix="0",
    ):
        metric = AIMetric.objects.create(
            session=self.session,
            source_type="screenshot",
            source_ref=f"/tmp/{suffix}.png",
            ocr_text_hash=None,
            feature_version="v1",
            features=features or {},
            productivity_score=productivity,
            anomaly_score=anomaly,
            anomaly_label=label,
            model_info=model_info or {},
            pipeline_status="ok",
            idempotency_key=f"idem-{suffix}",
            agent_timestamp=timezone.now(),
        )
        if created_at is not None:
            AIMetric.objects.filter(id=metric.id).update(created_at=created_at)
            metric.refresh_from_db()
        return metric

    def test_no_metrics_returns_zeroed_analytics(self):
        analytics = get_session_analytics(self.session.id, as_of=timezone.now())

        self.assertEqual(analytics["total_metrics"], 0)
        self.assertEqual(analytics["avg_productivity"], 0.0)
        self.assertEqual(analytics["avg_anomaly"], 0.0)
        self.assertEqual(analytics["suspicious_count"], 0)
        self.assertEqual(analytics["critical_count"], 0)
        self.assertEqual(analytics["anomaly_last_30min"], 0)
        self.assertEqual(analytics["critical_last_30min"], 0)
        self.assertEqual(analytics["baseline_mature_ratio"], 0.0)
        self.assertEqual(analytics["risk_level"], "LOW")

    def test_mixed_anomaly_labels_aggregate_counts_and_averages(self):
        self._create_metric(label="normal", productivity=80.0, anomaly=0.1, suffix="1")
        self._create_metric(label="suspicious", productivity=40.0, anomaly=0.6, suffix="2")
        self._create_metric(label="critical", productivity=20.0, anomaly=0.9, suffix="3")

        analytics = get_session_analytics(self.session.id, as_of=timezone.now())

        self.assertEqual(analytics["total_metrics"], 3)
        self.assertEqual(analytics["suspicious_count"], 1)
        self.assertEqual(analytics["critical_count"], 1)
        self.assertEqual(analytics["avg_productivity"], 46.67)
        self.assertEqual(analytics["avg_anomaly"], 0.5333)
        self.assertEqual(analytics["anomaly_last_30min"], 2)

    def test_recent_critical_spikes_escalate_to_high(self):
        as_of = timezone.now()

        self._create_metric(
            label="critical",
            anomaly=0.95,
            created_at=as_of - timedelta(minutes=5),
            suffix="4",
        )
        self._create_metric(
            label="critical",
            anomaly=0.96,
            created_at=as_of - timedelta(minutes=10),
            suffix="5",
        )
        self._create_metric(
            label="critical",
            anomaly=0.97,
            created_at=as_of - timedelta(minutes=20),
            suffix="6",
        )
        self._create_metric(
            label="critical",
            anomaly=0.98,
            created_at=as_of - timedelta(minutes=45),
            suffix="7",
        )

        analytics = get_session_analytics(self.session.id, as_of=as_of)

        self.assertEqual(analytics["critical_last_30min"], 3)
        self.assertEqual(analytics["critical_count"], 4)
        self.assertEqual(analytics["risk_level"], "HIGH")

    def test_baseline_mature_ratio_from_model_info(self):
        self._create_metric(
            label="normal",
            model_info={"anomaly_mode": "statistical"},
            suffix="8",
        )
        self._create_metric(
            label="normal",
            model_info={"anomaly_mode": "statistical"},
            suffix="9",
        )
        self._create_metric(
            label="normal",
            model_info={"anomaly_mode": "static"},
            suffix="10",
        )
        self._create_metric(label="normal", model_info={}, suffix="11")

        analytics = get_session_analytics(self.session.id, as_of=timezone.now())

        self.assertEqual(analytics["baseline_mature_ratio"], 0.5)

    def test_risk_escalation_logic_thresholds(self):
        self.assertEqual(resolve_risk_level(critical_last_30min=3, suspicious_last_30min=0), "HIGH")
        self.assertEqual(resolve_risk_level(critical_last_30min=2, suspicious_last_30min=5), "MEDIUM")
        self.assertEqual(resolve_risk_level(critical_last_30min=2, suspicious_last_30min=4), "LOW")

