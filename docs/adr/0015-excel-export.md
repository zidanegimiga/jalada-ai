# 0015. Excel export with openpyxl

Status: Accepted
Date: 2026-11-05

## Context
At filing time a user downloads one workbook for the tax year with five sheets that relate to the iTax return.

## Options considered
1. **CSV files.** Simple, but one table per file and no formatting or notes.
2. **XlsxWriter.** Fast and good formatting, but write-only.
3. **openpyxl.** Reads and writes, good formatting, widely used, and able to read the iTax template later if needed.
4. **Google Sheets API.** Live sharing, but needs a Google account and OAuth scopes, and is out of scope for now.

## Decision
openpyxl behind a `WorkbookWriter` port. The export is built from confirmed entries only, on request, and streamed back without being stored.

## Consequences
- Generation is synchronous. If it gets slow for large ledgers, it moves to a job.
- A Google Sheets adapter can come later on the same port.
