from pydantic import BaseModel, Field, field_validator
from datetime import datetime, date
from typing import List, Optional

class AuthorInBook(BaseModel):
    id: str
    name: str

class CategoryInBook(BaseModel):
    id: str
    name: str

class BookBase(BaseModel):
    # title: str
    # category_id: str
    # published_date: date
    # is_available: bool = True
    # author_ids: List[str]
    title: str = Field(..., max_length=200)
    category_id: str = Field(...)  # ObjectId length
    published_date: datetime
    is_available: bool = True
    author_ids: List[str] = Field(..., min_length=1)  # Ít nhất 1 author

    @field_validator('title')
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError('Title không được để trống')
        return v

    @field_validator('category_id')
    @classmethod
    def validate_category_id(cls, v: str) -> str:
        if len(v) != 24:
            raise ValueError('Category ID không hợp lệ')
        return v

    @field_validator('published_date')
    @classmethod
    def date_not_future(cls, v: datetime) -> datetime:
        if v.date() > date.today():  # So sánh date với date
            raise ValueError('Ngày xuất bản không được trong tương lai')
        return v

    @field_validator('author_ids')
    @classmethod
    def validate_author_ids(cls, v: List[str]) -> List[str]:
        for author_id in v:
            if len(author_id) != 24:
                raise ValueError(f'Author ID không hợp lệ: {author_id}')
        return list(set(v))

class BookCreate(BookBase):
    pass

class BookUpdate(BaseModel):
    title: Optional[str] = None
    category_id: Optional[str] = None
    published_date: Optional[datetime] = None
    is_available: Optional[bool] = None
    author_ids: Optional[List[str]] = None

class BookResponse(BaseModel):
    id: str
    title: str
    category_id: str
    published_date: datetime
    is_available: bool
    cover_image_url: Optional[str] = None

    # populated data
    category: Optional[CategoryInBook] = None
    authors: List[AuthorInBook] = []
