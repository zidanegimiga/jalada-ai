from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from jalada.domain.users import MAX_PASSWORD_LENGTH
from jalada.domain.users import User as DomainUser


class SignUpRequest(BaseModel):
    email: EmailStr
    password: str = Field(max_length=MAX_PASSWORD_LENGTH)
    display_name: str = Field(min_length=1, max_length=80)


class SignInRequest(BaseModel):
    email: EmailStr
    password: str = Field(max_length=MAX_PASSWORD_LENGTH)


class UserResponse(BaseModel):
    id: UUID
    email: str
    display_name: str

    @classmethod
    def from_user(cls, user: DomainUser) -> "UserResponse":
        return cls(id=user.id, email=user.email, display_name=user.display_name)
