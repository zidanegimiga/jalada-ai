"""Made-up M-Pesa messages moving money to and from a bank, for the transfer tests."""

import uuid
from collections.abc import Callable

TO_BANK = (
    "UK6CC1CC11 Confirmed. Ksh5,000.00 sent to SAMPLE BANK PAYBILL for account 0123456789 "
    "on 5/11/26 at 8:15 AM New M-PESA balance is Ksh1,000.00. Transaction cost, Ksh0.00."
)
AGAIN = TO_BANK.replace("UK6CC1CC11", "UK6CC1CC12").replace("Ksh5,000.00", "Ksh2,000.00")
OTHER_ACCOUNT = TO_BANK.replace("UK6CC1CC11", "UK6CC1CC13").replace("0123456789", "9876543210")
FROM_BANK = (
    "UK6CC1CC21 Confirmed.You have received Ksh3,000.00 from SAMPLE BANK 303030 "
    "on 5/11/26 at 9:15 AM New M-PESA balance is Ksh4,000.00."
)
FROM_BANK_AGAIN = FROM_BANK.replace("UK6CC1CC21", "UK6CC1CC22").replace("Ksh3,000", "Ksh1,000")
# Pastes a message for a user, reads it, and returns the payment's id.
Paste = Callable[..., uuid.UUID]
