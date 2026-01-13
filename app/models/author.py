# from sqlmodel import SQLModel, Field, Relationship
# from typing import List, Optional
# from app.models.book_author import BookAuthor  # import class
#
# class Author(SQLModel, table=True):
#     id: Optional[int] = Field(default=None, primary_key=True)
#     name: str = Field(max_length=100, nullable=False)
#     bio: Optional[str] = None
#
#     # Quan hệ N-N với Book
#     books: List["Book"] = Relationship(
#         back_populates="authors",
#         link_model=BookAuthor
#     )
