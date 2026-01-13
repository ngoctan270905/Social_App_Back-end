# from sqlmodel import SQLModel, Field, Relationship
# from typing import List, Optional
# from datetime import date
#
# from app.models.category import Category
# from app.models.author import Author
# from app.models.book_author import BookAuthor  # import class
#
# class Book(SQLModel, table=True):
#     id: Optional[int] = Field(default=None, primary_key=True)
#     title: str = Field(max_length=200, nullable=False)
#     category_id: int = Field(foreign_key="category.id")
#     published_date: date
#     is_available: bool = Field(default=True)
#     cover_image_url: Optional[str] = Field(default=None, max_length=255, nullable=True)
#
#     # Relationships
#     category: Optional[Category] = Relationship(back_populates="books")
#     authors: List[Author] = Relationship(
#         back_populates="books",
#         link_model=BookAuthor
#     )
