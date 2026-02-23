import re


class TextFeatureEngineer:
    """
    Converts raw text into structured numeric features.
    This is feature engineering — the heart of AI logic.
    """

    def redact(self, text: str) -> str:
        """
        Removes potentially sensitive information like emails and large numbers.
        """

        # Replace emails
        redacted = re.sub(
            r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
            "[EMAIL]",
            text,
        )

        # Replace large numbers
        redacted = re.sub(r"\b\d{3,}\b", "[NUMBER]", redacted)

        return redacted.strip()

    def extract(self, text: str) -> dict:
        """
        Converts cleaned text into numeric features.
        """

        words = re.findall(r"\w+", text.lower())
        lines = [line for line in text.splitlines() if line.strip()]

        focus_terms = {
            "jira", "ticket", "design", "spec",
            "review", "code", "build", "deploy",
            "Python", "Word"
        }

        distract_terms = {
            "youtube", "netflix", "game", "shopping", "JioHotstar", "Instagram"
        }

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
