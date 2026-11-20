from datetime import datetime

from pydantic import BaseModel, Field

from jalada.modules.accounts.api.schemas.auth import UserResponse


class DeviceCodeRequest(BaseModel):
    # The app's challenge: the SHA-256 of its secret verifier, unpadded base64url (RFC 7636).
    challenge: str = Field(min_length=43, max_length=43)


class DeviceCodeResponse(BaseModel):
    code: str
    expires_at: datetime


class DeviceTokenRequest(BaseModel):
    code: str = Field(min_length=1, max_length=100)
    verifier: str = Field(min_length=43, max_length=128)


class DeviceTokenResponse(BaseModel):
    """A session for the desktop app, sent back as a Bearer token on every request."""

    token: str
    expires_at: datetime
    user: UserResponse
