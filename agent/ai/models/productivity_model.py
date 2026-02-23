class ProductivityModel:
    """
    Rule-based productivity scoring model.
    Later this can be replaced with trained ML weights.
    """

    def predict(self, text: str, features: dict) -> float:
        base = 50.0

        # Reward focus keywords
        base += min(features["focus_keyword_hits"] * 6.0, 30.0)

        # Penalize distraction keywords
        base -= min(features["distraction_keyword_hits"] * 10.0, 40.0)

        # Penalize very small text
        if features["word_count"] < 3:
            base -= 10.0

        # Penalize empty screen
        if not text:
            base -= 15.0

        return round(max(0.0, min(100.0, base)), 2)
