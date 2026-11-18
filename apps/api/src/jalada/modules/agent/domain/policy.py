"""Questions the assistant refuses before any model sees them.

A model can be talked into saying what someone owes KRA, so these are answered by fixed text
instead. The patterns are narrow on purpose: "How much did I pay KRA?" is about a recorded
payment and still goes to the model.
"""

import re

TAX_OWED = re.compile(
    r"\b(tax|kra|paye|vat)\b.*\b(owe|due|payable|liable|should i pay|need to pay|have to pay)\b"
    r"|\b(owe|due|payable|liable|should i pay|need to pay|have to pay)\b.*\b(tax|kra)\b",
    re.I,
)
FILING = re.compile(r"\b(file|submit|lodge)\b.*\b(returns?|itax|kra)\b", re.I)
# Not "accounts": "my other account" is the person's own M-Pesa or bank account.
OTHER_PEOPLE = re.compile(
    r"\b(other|another|every|all)\b(\s+\w+)?\s+(users?|people|persons?|customers?)\b", re.I
)

TAX_ADVICE = (
    "I can't work out what tax is owed or give tax advice. I can show what is recorded, such "
    "as your income and costs, and your tax-year workbook is ready for you or a tax adviser."
)
NO_FILING = (
    "I can't file returns. You can download your tax-year workbook and file on iTax yourself, "
    "or give it to a tax adviser."
)
ONLY_YOURS = "I can only see your own records, never anyone else's."


def refusal_for(question: str) -> str | None:
    """The fixed reply when a question is one the assistant never answers, else None."""
    if OTHER_PEOPLE.search(question):
        return ONLY_YOURS
    if FILING.search(question):
        return NO_FILING
    if TAX_OWED.search(question):
        return TAX_ADVICE
    return None
