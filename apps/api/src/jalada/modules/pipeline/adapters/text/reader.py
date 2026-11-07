import io
from typing import Protocol

import pdfplumber
from pdfminer.pdfdocument import PDFPasswordIncorrect

from jalada.modules.pipeline.adapters.text.ocr import OcrText

# Below these, OCR output is too unreliable to parse, and the photo goes to the model instead.
MIN_OCR_CONFIDENCE = 60.0
MIN_OCR_CHARACTERS = 20


class ImageOcr(Protocol):
    def read(self, data: bytes) -> OcrText: ...


class EvidenceTextReader:
    """Text from pasted messages, PDFs that contain real text, and photos through OCR.

    Password-protected PDFs return None; their passwords are never stored.
    Photos return None when OCR is unsure, so the model reads the image itself.
    """

    def __init__(self, ocr: ImageOcr | None = None) -> None:
        self._ocr = ocr

    def read(self, content_type: str, data: bytes) -> str | None:
        if content_type.startswith("text/"):
            return data.decode("utf-8", errors="replace")
        if content_type == "application/pdf":
            return _pdf_text(data)
        if content_type.startswith("image/") and self._ocr:
            return _confident_text(self._ocr.read(data))
        return None


def _pdf_text(data: bytes) -> str | None:
    try:
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    except PDFPasswordIncorrect:
        return None
    return text if text.strip() else None


def _confident_text(result: OcrText) -> str | None:
    if result.confidence < MIN_OCR_CONFIDENCE or len(result.text) < MIN_OCR_CHARACTERS:
        return None
    return result.text
