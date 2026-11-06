import pytest
from samples import JPEG, PDF, PNG, WEBP

from jalada.modules.evidence.domain.evidence import detect_file_type, fingerprint


@pytest.mark.parametrize(
    ("data", "expected"),
    [(JPEG, "image/jpeg"), (PNG, "image/png"), (WEBP, "image/webp"), (PDF, "application/pdf")],
)
def test_accepted_files_are_recognised_by_their_first_bytes(data: bytes, expected: str) -> None:
    assert detect_file_type(data) == expected


@pytest.mark.parametrize(
    "data",
    [
        b"",
        b"hello world",
        b"<html><script>alert(1)</script>",
        b"MZ\x90\x00 an executable",
        b"XXXX\x00\x00\x00\x00WEBP",  # WEBP marker without the RIFF header
    ],
)
def test_everything_else_is_refused(data: bytes) -> None:
    assert detect_file_type(data) is None


def test_the_fingerprint_is_the_sha256_of_the_bytes() -> None:
    assert fingerprint(b"abc") == (
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    )
