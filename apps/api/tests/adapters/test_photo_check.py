import io

import pytest
from PIL import Image, ImageFilter
from samples import JPEG, make_receipt_photo

from jalada.modules.pipeline.adapters.text.photo_check import PillowPhotoCheck

LINES = ["MAMA PIMA GROCERS", "Date: 12/09/2026", "TOTAL KSH 480.00", "Paid: M-PESA"]


def blurred(radius: float) -> bytes:
    image = Image.open(io.BytesIO(make_receipt_photo(LINES))).filter(
        ImageFilter.GaussianBlur(radius)
    )
    out = io.BytesIO()
    image.save(out, "JPEG")
    return out.getvalue()


def test_a_clear_receipt_is_worth_reading() -> None:
    assert PillowPhotoCheck().problem(make_receipt_photo(LINES)) is None


@pytest.mark.parametrize("radius", [1, 2])
def test_a_slightly_soft_photo_still_goes_to_the_model(radius: float) -> None:
    assert PillowPhotoCheck().problem(blurred(radius)) is None


def test_a_photo_blurred_past_reading_is_stopped() -> None:
    assert PillowPhotoCheck().problem(blurred(4)) == "too blurred"


def test_a_tiny_photo_is_stopped() -> None:
    assert PillowPhotoCheck().problem(make_receipt_photo(LINES, noise=True)) == "too small"


def test_a_file_that_is_not_a_picture_is_stopped() -> None:
    assert PillowPhotoCheck().problem(JPEG) == "unreadable file"
