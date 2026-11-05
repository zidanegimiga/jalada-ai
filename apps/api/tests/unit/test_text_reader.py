import shutil

import pytest
from samples import JPEG, make_pdf, make_receipt_photo

from jalada.adapters.text.ocr import OcrText, TesseractOcr
from jalada.adapters.text.reader import EvidenceTextReader

needs_tesseract = pytest.mark.skipif(
    not shutil.which("tesseract"), reason="Tesseract not installed"
)


class FixedOcr:
    def __init__(self, text: str, confidence: float) -> None:
        self.result = OcrText(text, confidence)

    def read(self, data: bytes) -> OcrText:
        return self.result


def test_pasted_text_is_decoded() -> None:
    assert EvidenceTextReader().read("text/plain; charset=utf-8", b"Ksh 1,000") == "Ksh 1,000"


def test_text_is_read_out_of_a_pdf() -> None:
    pdf = make_pdf(["Withholding Certificate", "Gross Amount of Transaction (Ksh) 40,000.00"])

    text = EvidenceTextReader().read("application/pdf", pdf)

    assert text is not None
    assert "Withholding Certificate" in text
    assert "40,000.00" in text


def test_an_empty_pdf_gives_no_text() -> None:
    assert EvidenceTextReader().read("application/pdf", make_pdf([])) is None


def test_photos_give_no_text_without_ocr() -> None:
    assert EvidenceTextReader().read("image/jpeg", JPEG) is None


def test_confident_ocr_text_is_used() -> None:
    reader = EvidenceTextReader(FixedOcr("SAMPLE SHOP TOTAL KSh 250.00", 91.0))

    assert reader.read("image/jpeg", JPEG) == "SAMPLE SHOP TOTAL KSh 250.00"


def test_unsure_or_tiny_ocr_text_is_dropped_for_the_model() -> None:
    assert (
        EvidenceTextReader(FixedOcr("SAMPLE SHOP TOTAL 250", 41.0)).read("image/png", JPEG) is None
    )
    assert EvidenceTextReader(FixedOcr("KSh 250", 95.0)).read("image/png", JPEG) is None


@needs_tesseract
def test_tesseract_reads_a_receipt_photo() -> None:
    photo = make_receipt_photo(["SAMPLE SHOP", "Data bundle KSh 250.00", "TOTAL KSh 250.00"])

    result = TesseractOcr().read(photo)

    assert "SAMPLE SHOP" in result.text
    assert "250.00" in result.text
    assert result.confidence > 80


@needs_tesseract
def test_tesseract_is_unsure_about_an_unreadable_photo() -> None:
    photo = make_receipt_photo(["SAMPLE SHOP", "TOTAL KSh 250.00"], noise=True)

    assert EvidenceTextReader(TesseractOcr()).read("image/jpeg", photo) is None
