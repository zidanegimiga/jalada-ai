from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session as DbSession

from jalada.adapters.database.tables import CertificatePaymentRow


class SqlCertificatePayments:
    """Links between certificates and payments for one user. Every query filters by user."""

    def __init__(self, db: DbSession, user_id: UUID) -> None:
        self._db = db
        self._user_id = user_id

    def links(self) -> dict[UUID, UUID]:
        query = select(CertificatePaymentRow.payment_id, CertificatePaymentRow.certificate_id)
        rows = self._db.execute(query.where(CertificatePaymentRow.user_id == self._user_id))
        return {payment: certificate for payment, certificate in rows}

    def link(self, certificate_id: UUID, payment_id: UUID, at: datetime) -> None:
        # The primary key on payment_id makes a second link for the same payment fail.
        self._db.execute(
            insert(CertificatePaymentRow).values(
                payment_id=payment_id,
                certificate_id=certificate_id,
                user_id=self._user_id,
                linked_at=at,
            )
        )

    def unlink(self, certificate_id: UUID, payment_id: UUID) -> None:
        self._db.execute(
            delete(CertificatePaymentRow).where(
                CertificatePaymentRow.user_id == self._user_id,
                CertificatePaymentRow.certificate_id == certificate_id,
                CertificatePaymentRow.payment_id == payment_id,
            )
        )
