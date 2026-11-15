"""Whether a payment is ready to confirm as it is, which is what lets it into Confirm all.

The verifier must have passed it, so nothing it read is in doubt. Every category must be
the user's own or a rule's, never a model's suggestion. No question about it may be open,
such as a receipt that may belong to it. And confirming it must need no change (design 03,
"Confirming cheaply")."""

from jalada.modules.ledger.domain.payment_review import ReviewProblem, confirmed
from jalada.modules.ledger.domain.transactions import Transaction, TransactionStatus


def ready_to_confirm(payment: Transaction, open_question: bool) -> bool:
    if payment.status != TransactionStatus.PROPOSED or open_question:
        return False
    if any(line.suggested for line in payment.lines):
        return False
    try:
        confirmed(payment, payment.created_at)
    except ReviewProblem:
        return False
    return True
