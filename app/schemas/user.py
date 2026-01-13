# app/schemas/user.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


# ==================== Base Schema ====================
class UserBase(BaseModel):
    """Schema cơ sở cho User, chứa các trường chung"""
    username: str = Field(..., min_length=3, max_length=50, description="Tên đăng nhập")
    email: EmailStr = Field(..., description="Email của người dùng")
    is_active: Optional[bool] = True
    role: Optional[str] = Field("user", description="Vai trò của người dùng (user hoặc admin)")

    class Config:
        from_attributes = True


# ==================== Schema for Creation ====================
class UserCreate(UserBase):
    """Schema để tạo user mới, yêu cầu mật khẩu"""
    password: str = Field(..., min_length=6, description="Mật khẩu")


# ==================== Schema for Updating ====================
class UserUpdate(BaseModel):
    """Schema để cập nhật user, tất cả các trường đều là tùy chọn"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    role: Optional[str] = None
    password: Optional[str] = Field(None, min_length=6)


# ==================== Schema for Response ====================
class UserResponse(UserBase):
    """Schema để trả về trong API response, không bao gồm mật khẩu"""
    id: str
    created_at: datetime


# ==================== Schema for List Response ====================
class UserListResponse(BaseModel):
    """Schema để trả về danh sách user cùng với tổng số"""
    total: int
    users: List[UserResponse]

class UserChangePasswordRequest(BaseModel):
    """Schema for changing the current user's password."""
    old_password: str
    new_password: str = Field(..., min_length=6, max_length=100)
