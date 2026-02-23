from PIL import Image

try:
    import pytesseract
except Exception:
    pytesseract = None


class OCRExtractor:
    """
    Responsible ONLY for extracting raw text from an image.
    No scoring.
    No feature logic.
    No AI decisions.
    """

    def extract_text(self, image_path: str) -> tuple[str, str | None, str | None]:
        """
        Extracts text from a screenshot.

        Returns:
            text: extracted OCR text (empty string if unavailable)
            error_code: machine-readable error code (or None)
            error_message: human-readable error message (or None)
        """

        # If pytesseract is not available in the environment
        if pytesseract is None:
            return "", "OCR_UNAVAILABLE", "pytesseract is not installed"

        try:
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image)
            return text, None, None

        except Exception as exc:
            return "", "OCR_ERROR", str(exc)
