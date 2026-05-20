from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole


class UserRegister(BaseModel):
    email: EmailStr = Field(
        ...,
        description="User email address. Used as the login identifier. Must be unique.",
        examples=["victor@bankercrm.dev"],
    )
    password: str = Field(
        ...,
        min_length=8,
        description=(
            "User password. Stored as a bcrypt hash — never in plain text. Minimum 8 characters."
        ),
        examples=["Secure1234!"],
    )
    role: UserRole = Field(
        default=UserRole.READ_ONLY,
        description=(
            "Role assigned to the user. Defaults to `read_only` if not specified. "
            "Use `admin` for full access or `analyst` for write access to clients and accounts."
        ),
        examples=["read_only"],
    )


class UserResponse(BaseModel):
    id: int = Field(..., description="Auto-generated unique user ID.", examples=[1])
    email: str = Field(..., examples=["victor@bankercrm.dev"])
    role: UserRole = Field(..., description="Role assigned to this user.", examples=["admin"])
    is_active: bool = Field(
        ...,
        description="`false` if the user has been deactivated.",
    )

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str = Field(
        ...,
        description=(
            "Short-lived JWT for authenticating requests. "
            "Include in the `Authorization: Bearer <token>` header. "
            "Expires after 30 minutes."
        ),
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."],
    )
    refresh_token: str = Field(
        ...,
        description=(
            "Long-lived token used to obtain a new `access_token` without re-login. "
            "Valid for 7 days. Rotated on every use — the previous token is invalidated immediately."
        ),
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."],
    )
    token_type: str = Field(
        default="bearer",
        description="Token scheme. Always `bearer`.",
    )


class RefreshRequest(BaseModel):
    refresh_token: str = Field(
        ...,
        description=(
            "The refresh token obtained during login or a previous refresh call. "
            "Rotated on every use — store the new token returned in the response."
        ),
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."],
    )
