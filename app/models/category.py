# from typing import List, Optional
#
# from sqlmodel import SQLModel, Field, Relationship
#
#
# class Category(SQLModel, table=True):
#     id: Optional[int] = Field(default=None, primary_key=True)
#     name: str = Field(max_length=100, unique=True, nullable=False)
#
#     # Quan hệ 1-N với Book
#     books: List["Book"] = Relationship(back_populates="category")
