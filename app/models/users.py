# from typing import Optional, List
# from sqlmodel import SQLModel, Field, Relationship
# from datetime import datetime
# from app.core.timezone import now_vn
#
# # Import OAuthAccount and forward reference it if necessary
# # This avoids circular imports but allows type hinting
# class OAuthAccount(SQLModel):
#     pass
#
# # Forward reference for the new RefreshToken model
# class RefreshToken(SQLModel):
#     pass
#
# class User(SQLModel, table=True):
#     id: Optional[int] = Field(default=None, primary_key=True)
#     username: str = Field(max_length=50, nullable=False, unique=True, index=True)
#     email: str = Field(max_length=100, nullable=False, unique=True, index=True)
#     hashed_password: Optional[str] = Field(default=None, nullable=True) # Made nullable
#     is_active: bool = Field(default=True)
#     role: Optional[str] = Field(default="user", max_length=20) # Kept the role
#     email_verified: bool = Field(default=False)
#     created_at: datetime = Field(default_factory=now_vn)
#     updated_at: datetime = Field(default_factory=now_vn, sa_column_kwargs={"onupdate": now_vn})
#
#     oauth_accounts: List["OAuthAccount"] = Relationship(back_populates="user")
#     refresh_tokens: List["RefreshToken"] = Relationship(back_populates="user")
#
#     @property
#     def is_social_login(self) -> bool:
#         """Returns True if the user signed up via a social provider."""
#         return self.hashed_password is None
