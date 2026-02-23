import math


MIN_BASELINE_SAMPLES = 10


class AnomalyModel:
    """
    Hybrid anomaly detection:
    - Uses statistical z-score detection when baseline mature
    - Falls back to static rule-based logic when immature
    """

    def __init__(self, baseline_store):
        self.baseline = baseline_store

    # ------------------------------------
    # Public API
    # ------------------------------------

    def score(self, features: dict) -> float:
        """
        Returns anomaly score between 0.0 and 1.0
        """

        if self._baseline_ready():
            return self._statistical_anomaly(features)

        return self._static_anomaly(features)
    
    # ------------------------------------
    # Labeling
    # ------------------------------------

    def label(self, anomaly_score: float) -> str:
        """
        Converts anomaly score into categorical label.
        """

        if anomaly_score >= 0.75:
            return "critical"

        if anomaly_score >= 0.4:
            return "suspicious"

        return "normal"
    
    def evaluate(self, features: dict):
        """
        Returns:
            anomaly_score (float),
            explanation (dict)
        """

        if self._baseline_ready():
            return self._evaluate_statistical(features)

        return self._evaluate_static(features)
    
    def _evaluate_statistical(self, features: dict):

        z_scores = {}
        collected = []

        for key in features_tracked():
            value = features.get(key)
            if value is None:
                continue

            z = self.baseline.z_score(key, value)
            z_scores[key] = round(z, 3)
            collected.append(z)

        if not collected:
            return 0.0, {"mode": "statistical", "details": {}}

        avg_z = sum(collected) / len(collected)
        normalized = min(avg_z / 3.0, 1.0)

        return (
            round(normalized, 3),
            {
                "mode": "statistical",
                "avg_z": round(avg_z, 3),
                "feature_z_scores": z_scores,
            },
        )
    
    def _evaluate_static(self, features: dict):

        score = 0.1
        triggers = []

        if features.get("word_count", 0) < 2:
            score += 0.4
            triggers.append("low_word_count")

        if features.get("alpha_ratio", 1.0) < 0.2:
            score += 0.3
            triggers.append("low_alpha_ratio")

        if features.get("distraction_keyword_hits", 0) > 1:
            score += 0.3
            triggers.append("multiple_distractions")

        return (
            round(min(score, 1.0), 3),
            {
                "mode": "static",
                "triggers": triggers,
            },
        )

    # ------------------------------------
    # Baseline Logic
    # ------------------------------------

    def _baseline_ready(self) -> bool:
        """
        Baseline considered ready if any tracked feature
        has sufficient sample size.
        """
        for key in features_tracked():
            stats = self.baseline.get_stats(key)
            if stats and stats["count"] >= MIN_BASELINE_SAMPLES:
                return True
        return False

    # ------------------------------------
    # Statistical Anomaly
    # ------------------------------------

    def _statistical_anomaly(self, features: dict) -> float:
        """
        Uses z-score across selected features.
        """

        z_scores = []

        for key in features_tracked():
            value = features.get(key)
            if value is None:
                continue

            z = self.baseline.z_score(key, value)
            z_scores.append(z)

        if not z_scores:
            return 0.0

        # Convert average z-score into 0–1 scale
        avg_z = sum(z_scores) / len(z_scores)

        # Normalize:
        # z >= 3 → strong anomaly (≈1.0)
        normalized = min(avg_z / 3.0, 1.0)

        return round(normalized, 3)

    # ------------------------------------
    # Static Fallback
    # ------------------------------------

    def _static_anomaly(self, features: dict) -> float:
        """
        Simple heuristic rules (previous behavior).
        """

        score = 0.1

        if features.get("word_count", 0) < 2:
            score += 0.4

        if features.get("alpha_ratio", 1.0) < 0.2:
            score += 0.3

        if features.get("distraction_keyword_hits", 0) > 1:
            score += 0.3

        return round(min(score, 1.0), 3)


# ------------------------------------
# Utility
# ------------------------------------

def features_tracked():
    return [
        "word_count",
        "focus_keyword_hits",
        "distraction_keyword_hits",
        "alpha_ratio",
    ]
