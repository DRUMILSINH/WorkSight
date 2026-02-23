import math
import json
from pathlib import Path


class BaselineStore:
    """
    Maintains running statistics (mean + std) for numeric features.
    Uses Welford's online algorithm for stability.
    """

    def __init__(self, storage_path: str):
        self.path = Path(storage_path)
        self.data = self._load()

    # ---------------------------
    # Public API
    # ---------------------------

    def update(self, features: dict):
        """
        Update baseline statistics with new feature values.
        Only numeric features are tracked.
        """

        for key, value in features.items():
            if not isinstance(value, (int, float)):
                continue

            stats = self.data.setdefault(
                key,
                {"count": 0, "mean": 0.0, "M2": 0.0},
            )

            stats["count"] += 1
            count = stats["count"]

            delta = value - stats["mean"]
            stats["mean"] += delta / count
            delta2 = value - stats["mean"]
            stats["M2"] += delta * delta2

        self._save()

    def get_stats(self, feature_name: str):
        """
        Returns mean, std, count for a feature.
        """
        stats = self.data.get(feature_name)

        if not stats or stats["count"] < 2:
            return None

        variance = stats["M2"] / (stats["count"] - 1)
        std = math.sqrt(variance) if variance > 0 else 0.0

        return {
            "mean": stats["mean"],
            "std": std,
            "count": stats["count"],
        }

    def z_score(self, feature_name: str, value: float):
        """
        Computes z-score for a feature value.
        """
        stats = self.get_stats(feature_name)

        if not stats or stats["std"] == 0:
            return 0.0

        return abs(value - stats["mean"]) / stats["std"]

    # ---------------------------
    # Persistence
    # ---------------------------

    def _load(self):
        if not self.path.exists():
            return {}

        try:
            return json.loads(self.path.read_text())
        except Exception:
            return {}

    def _save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data))
