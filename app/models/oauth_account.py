# from typing import List, Optional
# from sqlmodel import Field, SQLModel, Relationship
#
# class OAuthAccount(SQLModel, table=True):
#     id: Optional[int] = Field(default=None, primary_key=True)
#     provider: str = Field(index=True) # e.g., "google", "github"
#     account_id: str = Field(index=True) # unique ID from the OAuth provider
#     access_token: str # encrypted or not
#     # Potentially add refresh_token, expires_at, etc.
#
#     user_id: Optional[int] = Field(default=None, foreign_key="user.id")
#     user: Optional["User"] = Relationship(back_populates="oauth_accounts")
#
# # Deferred import to avoid circular dependency
# from .users import User
# User.update_forward_refs()
