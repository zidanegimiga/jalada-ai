from typing import Self

from fastapi import APIRouter
from pydantic import BaseModel

from jalada.dependencies import CurrentUser, ServicesDependency
from jalada.modules.accounts.domain.consent import ConsentStatus

router = APIRouter(tags=["account"])


class ConsentResponse(BaseModel):
    # False when no model is set up: there is nothing to agree to.
    required: bool
    given: bool
    # Who reads the records, where, and on what terms.
    notice: str

    @classmethod
    def from_status(cls, status: ConsentStatus) -> Self:
        return cls(required=status.required, given=status.given, notice=status.notice)


@router.get("/v1/account/model-consent")
def read_model_consent(user: CurrentUser, services: ServicesDependency) -> ConsentResponse:
    """Whether a model may read this person's receipts, messages and questions."""
    return ConsentResponse.from_status(services.model_consent.status(user.id))


@router.post("/v1/account/model-consent")
def give_model_consent(user: CurrentUser, services: ServicesDependency) -> ConsentResponse:
    return ConsentResponse.from_status(services.model_consent.give(user.id))


@router.delete("/v1/account/model-consent")
def withdraw_model_consent(user: CurrentUser, services: ServicesDependency) -> ConsentResponse:
    """From now on, rules and OCR alone read new evidence, and the assistant stops answering."""
    return ConsentResponse.from_status(services.model_consent.withdraw(user.id))


class PrivacyResponse(BaseModel):
    # Who reads records with AI, for those who agree; None when no model is set up.
    model_provider: str | None


@router.get("/v1/privacy")
def read_privacy(services: ServicesDependency) -> PrivacyResponse:
    """What the privacy notice names that depends on how the app is set up. Public."""
    return PrivacyResponse(model_provider=services.model_consent.notice)
