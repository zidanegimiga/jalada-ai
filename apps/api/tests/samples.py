"""Tiny made-up files with real signatures, for upload tests."""

JPEG = b"\xff\xd8\xff\xe0" + b"\x00\x10JFIF" + b"\x00" * 50
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 50
WEBP = b"RIFF\x24\x00\x00\x00WEBPVP8 " + b"\x00" * 50
PDF = b"%PDF-1.7\n" + b"0" * 50
MPESA = (
    "UK4AB1CD25 Confirmed.You have received Ksh1,000.00 from EXAMPLE BANK 1 500000 "
    "on 4/11/26 at 4:44 PM New M-PESA balance is Ksh2,211.58."
)
