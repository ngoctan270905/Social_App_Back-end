# from datetime import datetime
# from typing import Optional, List
# from sqlmodel import Field, Relationship, SQLModel
#
# # Forward declaration to avoid circular imports
# class User(SQLModel):
#     pass
#
# class RefreshToken(SQLModel, table=True):
#     __tablename__ = "refresh_tokens"
#
#     id: Optional[int] = Field(default=None, primary_key=True)
#     token: str = Field(unique=True, index=True)
#     user_id: int = Field(foreign_key="user.id")
#     expires_at: datetime
#     created_at: datetime = Field(default_factory=datetime.utcnow)
#     revoked_at: Optional[datetime] = Field(default=None)
#
#     user: "User" = Relationship(back_populates="refresh_tokens")
