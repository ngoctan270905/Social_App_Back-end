from typing import List, Tuple, Optional, Dict, Any
from fastapi import HTTPException, status
from unicodedata import category
from app.repositories.author_repository import AuthorRepository
from app.repositories.book_repository import BookRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.author_repository import AuthorRepository
from app.schemas.book import BookCreate, BookUpdate, BookResponse, AuthorInBook, CategoryInBook


class BookService:

    # Hàm khởi tạo
    def __init__(self, book_repo: BookRepository, author_repo: AuthorRepository, category_repo: CategoryRepository):
        self.book_repo = book_repo
        self.author_repo = author_repo
        self.category_repo = category_repo


    # hàm map ObjectId sang str
    def map_id(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if '_id' in data:
            data['id'] = str(data['_id'])
            del data['_id']
        return data


    # logic lấy ds book kèm quan hệ author và category
    async def get_all_books(self) -> List[BookResponse]:
        books_list_dict = await self.book_repo.get_all()

        books = []
        for book_dict in books_list_dict:
            book_data = self.map_id(book_dict)

            # lấy thông tin category
            if book_data.get('category_id'):
                category_dict = await self.category_repo.get_by_category_id(book_data['category_id'])
                if category_dict:
                    category_data = self.map_id(category_dict)
                    book_data['category'] = CategoryInBook(
                        id=category_data['id'],
                        name=category_data['name']
                    )

            # lấy thông tin authors
            if book_data.get('author_ids'):
                authors = []
                for author_id in book_data['author_ids']:
                    author_dict = await self.author_repo.get_by_id(author_id)
                    if author_dict:
                        author_data = self.map_id(author_dict)
                        authors.append(AuthorInBook(
                            id=author_data['id'],
                            name=author_data['name']
                        ))
                book_data['authors'] = authors

            book_response = BookResponse(**book_data)
            books.append(book_response)

        return books


    # Logic thêm book mới
    async def create_new_book(self, book_create: BookCreate) -> BookResponse:
        existing_book = await self.book_repo.get_book_by_name(book_create.title)
        if existing_book:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Book '{book_create.title}' đã tồn tại"
            )
        category_dict = await self.category_repo.get_by_category_id(book_create.category_id)
        if not category_dict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category '{book_create.category_id}' không tồn tại"
            )
        authors_list = []
        for author_id in book_create.author_ids:
            author_dict = await self.author_repo.get_by_id(author_id)
            if not author_dict:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Author '{author_id}' không tồn tại"
                )
            authors_list.append(AuthorInBook(
                id=str(author_dict['_id']),
                name=author_dict['name']
            ))
        new_book_dict = await self.book_repo.create_book(book_create)
        book_data = self.map_id(new_book_dict)

        book_data['category'] = CategoryInBook(
            id=str(category_dict['_id']),
            name=category_dict['name']
        )
        book_data['authors'] = authors_list
        return BookResponse(**book_data)


    # Logic xem chi tiết book
    async def get_book_detail(self, book_id: str) -> Optional[BookResponse]:
        book_dict = await self.book_repo.get_by_book_id(book_id)
        if not book_dict:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Book không tồn tại"
            )

        book_data = self.map_id(book_dict)
        if book_data.get('category_id'):
            category_dict = await self.category_repo.get_by_category_id(book_data['category_id'])
            if category_dict:
                category_data = self.map_id(category_dict)
                book_data['category'] = CategoryInBook(
                    id=category_data['id'],
                    name=category_data['name']
                )
        if book_data.get('author_ids'):
            authors = []
            for author_id in book_data['author_ids']:
                author_dict = await self.author_repo.get_by_id(author_id)
                if author_dict:
                    author_data = self.map_id(author_dict)
                    authors.append(AuthorInBook(
                        id=author_data['id'],
                        name=author_data['name']
                    ))
            book_data['authors'] = authors
        return BookResponse(**book_data)


    # Logic update book
    async def update_book(self, book_id: str, book_update: BookUpdate) -> Optional[BookResponse]:
        existing_book = await self.book_repo.get_by_book_id(book_id)
        if not existing_book:
            return None
        updated_book_dict = await self.book_repo.update_book(book_id, book_update)
        book_data = self.map_id(updated_book_dict)
        return BookResponse(**book_data)


   # Logic delete Book
    async def delete_book(self, book_id: str) -> bool:
        deleted_book = await self.book_repo.delete_book(book_id)
        return deleted_book
