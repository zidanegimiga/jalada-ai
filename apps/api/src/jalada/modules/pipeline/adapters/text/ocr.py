import io
from dataclasses import dataclass

import pytesseract
from PIL import Image, ImageOps

# Photos smaller than this are enlarged first. Tesseract reads small text badly.
MIN_WIDTH = 1200


@dataclass(frozen=True)
class OcrText:
    text: str
    # Mean word confidence from Tesseract, 0 to 100.
    confidence: float


class TesseractOcr:
    """Reads text out of photos of receipts and screenshots."""

    def read(self, data: bytes) -> OcrText:
        image = _prepare(Image.open(io.BytesIO(data)))
        words = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        scores = [
            float(score)
            for score, word in zip(words["conf"], words["text"], strict=True)
            if word.strip() and float(score) >= 0
        ]
        text = pytesseract.image_to_string(image)
        return OcrText(text.strip(), sum(scores) / len(scores) if scores else 0.0)


def _prepare(image: Image.Image) -> Image.Image:
    # Phones store rotation in EXIF; apply it so the text is upright.
    image = ImageOps.exif_transpose(image) or image
    image = ImageOps.grayscale(image)
    if image.width < MIN_WIDTH:
        scale = MIN_WIDTH / image.width
        image = image.resize((MIN_WIDTH, int(image.height * scale)), Image.Resampling.LANCZOS)
    return image
