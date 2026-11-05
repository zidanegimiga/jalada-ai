# 0013. Text extraction: pdfplumber and Tesseract

Status: Accepted
Date: 2026-11-05

## Context
Rules can only parse evidence once it is text. PDFs often contain real text. Photos need OCR (optical character recognition, turning an image of text into text).

## Options considered
For PDFs:
1. **pypdf.** Small, but loses layout, which matters for tables in statements and certificates.
2. **pdfplumber.** Keeps positions, so table rows can be rebuilt.

For images:
1. **Tesseract.** Mature, free, a system package in the Docker image, and light on memory.
2. **PaddleOCR.** Often more accurate on photos, but large models and heavy memory use on free hosts.
3. **A vision model through the model port.** Most accurate on messy photos, but costs tokens on every image.

## Decision
`TextFromPdf` with pdfplumber and `TextFromImage` with Tesseract, called through pytesseract. When OCR confidence is low, the extractor falls back to the vision model through the `LanguageModel` port, within the run's budget.

## Consequences
- The worker image gains the Tesseract system package, about 30 MB.
- Password-protected M-Pesa statements are opened in memory with the password the user types, which is never stored.
- PaddleOCR can be added later as a second adapter if photos prove hard.
