import io

import pdfplumber
from pdfminer.pdfdocument import PDFPasswordIncorrect


class PlainAndPdfTextReader:
    """Text from pasted messages and from PDFs that contain real text.

    Images return None for now, so they go to review until OCR is added.
    Password-protected PDFs also return None; their passwords are never stored.
    """

    def read(self, content_type: str, data: bytes) -> str | None:
        if content_type.startswith("text/"):
            return data.decode("utf-8", errors="replace")
        if content_type == "application/pdf":
            return _pdf_text(data)
        return None


def _pdf_text(data: bytes) -> str | None:
    try:
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    except PDFPasswordIncorrect:
        return None
    return text if text.strip() else None
