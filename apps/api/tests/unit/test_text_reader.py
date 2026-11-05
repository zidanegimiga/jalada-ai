from samples import make_pdf

from jalada.adapters.text.reader import PlainAndPdfTextReader


def test_pasted_text_is_decoded() -> None:
    assert PlainAndPdfTextReader().read("text/plain; charset=utf-8", b"Ksh 1,000") == ("Ksh 1,000")


def test_text_is_read_out_of_a_pdf() -> None:
    pdf = make_pdf(["Withholding Certificate", "Gross Amount of Transaction (Ksh) 40,000.00"])

    text = PlainAndPdfTextReader().read("application/pdf", pdf)

    assert text is not None
    assert "Withholding Certificate" in text
    assert "40,000.00" in text


def test_images_and_broken_pdfs_give_no_text() -> None:
    reader = PlainAndPdfTextReader()

    assert reader.read("image/jpeg", b"\xff\xd8\xff") is None
    assert reader.read("application/pdf", make_pdf([])) is None
