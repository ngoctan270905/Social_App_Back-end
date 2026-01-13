from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Literal
from datetime import datetime
from .utils import ObjectIdStr

# Định dạng dữ liệu đăng kí tài khoản khi client gửi lên ===============================================================
class UserRegister(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    day: int = Field(..., ge=1, le=31, description="Ngày sinh")
    month: int = Field(..., ge=1, le=12, description="Tháng sinh")
    year: int = Field(..., ge=1905, le=2026, description="Năm sinh")
    gender: Literal['male', 'female']
    email: EmailStr = Field(..., max_length=254)
    password: str = Field(..., min_length=6, max_length=100)


# Định dạng dữ liệu trả về cho client ==================================================================================
class UserRegisterResponse(BaseModel):
    email: EmailStr


# Định dạng dữ liệu thông tin User trả về cho Client ===================================================================
class UserMeResponse(BaseModel):
    id: Optional[ObjectIdStr] = Field(default=None, alias="_id", serialization_alias="id")
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    email: EmailStr
    avatar: Optional[str] = None
    created_at: datetime

# Định dạng dữ liệu xác minh email =====================================================================================
class EmailVerificationRequest(BaseModel):
    email: EmailStr = Field(...)
    otp: str = Field(...)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=6, max_length=100)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[str] = None
    username: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    is_active: bool
    role: str
    email_verified: bool
    is_social_login: bool
    created_at: datetime
    updated_at: datetime

class ResendVerificationRequest(BaseModel):
    email: EmailStr

class VerifyForgotPasswordRequest(BaseModel):
    email: EmailStr
    otp: str
