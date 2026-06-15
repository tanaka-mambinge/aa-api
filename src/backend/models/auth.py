from datetime import datetime
from enum import Enum

from pydantic import BaseModel, EmailStr, Field


class DeviceType(str, Enum):
    WEB = "web"
    CLI = "cli"
    APP = "app"
    OTHER = "other"


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    device_type: DeviceType = DeviceType.WEB


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    device_type: DeviceType = DeviceType.WEB


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=8, max_length=128)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=1)
    new_password: str = Field(min_length=8, max_length=128)


class AuthResponse(BaseModel):
    access_token: str | None = None
    token_type: str | None = None
    user: "UserResponse"


class UserResponse(BaseModel):
    id: str
    workspace_id: str
    name: str
    email: EmailStr
    created_at: datetime


class CliTokenCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    expires_in_days: int | None = Field(default=None, ge=1, le=365)


class CliTokenResponse(BaseModel):
    id: str
    name: str
    token_prefix: str
    last_used_at: datetime | None
    expires_at: datetime | None
    revoked_at: datetime | None
    created_at: datetime


class CliTokenCreateResponse(CliTokenResponse):
    token: str
