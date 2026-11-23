from typing import Optional

from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    display_name: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    role: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class ChangeUsernameRequest(BaseModel):
    password: str
    new_username: str


class MeResponse(BaseModel):
    id: int
    username: str
    display_name: Optional[str] = None
    role: str


class AuthSettings(BaseModel):
    allow_register: bool = False
