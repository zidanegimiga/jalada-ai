# Withholding tax certificates

Layout of the certificate a payer downloads from iTax after withholding tax. All values below are invented.

The certificate is a one-page PDF with real text, so pdfplumber reads it without OCR. Its main content is a two-column table of labels and values.

| Label on the certificate | Example value | Field |
| --- | --- | --- |
| Date of Certificate | 11/03/2026 | certificate date, DD/MM/YYYY |
| Certificate Serial Number | KRAWHTEON0000000000 | `certificate_serial`, the duplicate key |
| PIN of Withholder | P000000000A | payer tax number |
| Name of Withholder | EXAMPLE CONSULTING LTD | payer, the counterparty |
| Address of Withholder | (several lines) | ignored |
| PIN of Withholdee (If available) | A000000000Z | the user's own tax number |
| Name of Withholdee | JANE WANJIKU | the user |
| Address of Withholdee | (several lines) | ignored |
| Nature of Transaction | Management, Professional Training or Consultancy Fees Which Is Over 24,000 In A Month | nature, used to suggest a category |
| Transaction Date | 03/03/2026 | `occurred_on`, DD/MM/YYYY |
| Gross Amount of Transaction (Ksh) | 40,000.00 | `amount_cents` |
| Withholding Tax Rate | 5.00 | rate in percent |
| Amount of Tax Withheld (Ksh) | 2,000.00 | `tax_withheld_cents` |

Checks the verifier can make:

- Gross amount times the rate equals the tax withheld, to the cent.
- The serial number starts with `KRAWHT`.
- The transaction date is on or before the certificate date.

A certificate records income that was earned and tax already paid on it. It is entered as a `withholding_certificate` entry with direction in. If the same payment also arrives as an M-Pesa or bank deposit, the deposit is the net amount (gross minus tax), and the two should be linked rather than counted twice. How to link them is an open design point.

Notes from the certificate wording: it says the tax was "deposited to the collector of Income tax", and that its authenticity can be checked on the iTax portal with the certificate number.
