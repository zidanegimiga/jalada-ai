"""Tiny made-up files with real signatures, for upload tests."""

JPEG = b"\xff\xd8\xff\xe0" + b"\x00\x10JFIF" + b"\x00" * 50
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 50
WEBP = b"RIFF\x24\x00\x00\x00WEBPVP8 " + b"\x00" * 50
PDF = b"%PDF-1.7\n" + b"0" * 50
MPESA = (
    "UK4AB1CD25 Confirmed.You have received Ksh1,000.00 from EXAMPLE BANK 1 500000 "
    "on 4/11/26 at 4:44 PM New M-PESA balance is Ksh2,211.58."
)

MPESA_SENT = (
    "UK5AB1CD23 Confirmed. Ksh150.00 sent to JANE  WANJIKU 0712345678 on 5/11/26 at 2:43 PM. "
    "New M-PESA balance is Ksh2,339.58. Transaction cost, Ksh7.00.  Amount you can transact "
    "within the day is 496,142.00. See all your balances now https://example.com/abc"
)
MPESA_PAYBILL = (
    "UK5AB1CD24 Confirmed. Ksh419.00 sent to M-PESA CARD for account Paystack-Shop-Music   "
    "+254700000000KE on 5/11/26 at 2:32 PM New M-PESA balance is Ksh2,496.58. Transaction cost, "
    "Ksh0.00.Amount you can transact within the day is 496,292.00. See all your balances now "
    "https://example.com/def"
)
CERTIFICATE = """Withholding Certificate
Date of Certificate: 11/03/2026
Certificate Serial Number:
KRAWHTEON0000000001
Withholder Details
PIN of Withholder P000000000A
Name of Withholder EXAMPLE CONSULTING LTD
Withholdee Details
PIN of Withholdee (If available) A000000000Z
Name of Withholdee JANE WANJIKU
Details of Tax Withheld
Management, Professional Training or Consultancy Fees
Nature of Transaction
Which Is Over 24,000 In A Month
Transaction Date 03/03/2026
Gross Amount of Transaction (Ksh) 40,000.00
Withholding Tax Rate 5.00
Amount of Tax Withheld (Ksh) 2,000.00
"""


def make_pdf(lines: list[str]) -> bytes:
    """A minimal one-page PDF with real text, for testing the PDF reader."""
    escaped = [line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)") for line in lines]
    text = "BT /F1 11 Tf 40 800 Td 14 TL " + " ".join(f"({line}) '" for line in escaped) + " ET"
    objects = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R "
        "/Resources << /Font << /F1 5 0 R >> >> >>",
        f"<< /Length {len(text)} >>\nstream\n{text}\nendstream",
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out, offsets = b"%PDF-1.4\n", []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{number} 0 obj\n{body}\nendobj\n".encode()
    xref = len(out)
    out += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    out += b"".join(f"{o:010d} 00000 n \n".encode() for o in offsets)
    out += f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF".encode()
    return out


def make_receipt_photo(lines: list[str], noise: bool = False) -> bytes:
    """A JPEG of printed text, like a phone photo of a receipt. `noise` makes it unreadable."""
    import io
    import random

    from PIL import Image, ImageDraw, ImageFont

    image = Image.new("RGB", (900, 120 + 70 * len(lines)), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=44)
    for row, line in enumerate(lines):
        draw.text((60, 60 + 70 * row), line, fill="black", font=font)
    if noise:
        pixels = random.Random(7)  # noqa: S311 (seeded noise for a test image, not security)
        for _ in range(60000):
            draw.point((pixels.randrange(image.width), pixels.randrange(image.height)), "black")
        image = image.resize((90, image.height // 10))
    out = io.BytesIO()
    image.save(out, "JPEG", quality=85)
    return out.getvalue()
