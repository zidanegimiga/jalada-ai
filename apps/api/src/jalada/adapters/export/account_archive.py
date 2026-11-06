import json
import zipfile
from collections.abc import Iterator
from dataclasses import asdict
from typing import IO, Any

from jalada.application.account_export import AccountData
from jalada.domain.evidence import Evidence

EXTENSIONS = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "application/pdf": "pdf",
}

README = """Your Jalada AI data

account.json          your name, email and when you joined
evidence.json         everything you sent, with where to find each original in this folder
evidence/             the originals: photos, PDFs and messages, exactly as you sent them
entries.json          every ledger entry, confirmed or not, amounts in cents
entry_revisions.json  each confirmation or correction, with the entry before and after
pipeline_runs.json    how each piece of evidence was read, step by step
preferences.json      the categories you chose for people and businesses you pay
certificate_payments.json  payments you linked to withholding certificates, by entry id

Amounts are in cents: 125000 means KSh 1,250.00.
"""


def file_name(item: Evidence) -> str:
    extension = EXTENSIONS.get(item.content_type, "txt")
    return f"evidence/{item.received_at:%Y-%m-%d}_{item.id}.{extension}"


class ZipAccountArchive:
    content_type = "application/zip"
    extension = "zip"

    def write(
        self, data: AccountData, originals: Iterator[tuple[Evidence, bytes]], out: IO[bytes]
    ) -> None:
        with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("README.txt", README)
            archive.writestr(
                "account.json",
                _json({**asdict(data.user), "telegram_linked": data.telegram_linked}),
            )
            archive.writestr(
                "evidence.json", _json([{**asdict(e), "file": file_name(e)} for e in data.evidence])
            )
            archive.writestr("entries.json", _json([asdict(e) for e in data.entries]))
            archive.writestr("entry_revisions.json", _json([asdict(r) for r in data.revisions]))
            archive.writestr(
                "pipeline_runs.json",
                _json(
                    [
                        {**asdict(run), "steps": [asdict(s) for s in steps]}
                        for run, steps in data.runs
                    ]
                ),
            )
            archive.writestr(
                "preferences.json",
                _json({key: asdict(choice) for key, choice in data.preferences.items()}),
            )
            archive.writestr(
                "certificate_payments.json",
                _json(
                    [
                        {"payment_entry_id": payment, "certificate_entry_id": certificate}
                        for payment, certificate in data.certificate_payments.items()
                    ]
                ),
            )
            for item, content in originals:
                archive.writestr(file_name(item), content)


def _json(value: Any) -> str:
    # Dates, ids and decimals become plain text, so any program can read the file.
    return json.dumps(value, indent=2, default=str, ensure_ascii=False)
