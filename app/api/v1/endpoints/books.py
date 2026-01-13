from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from app.core.database import get_session
from app.services.book_service import BookService
from app.schemas.book import BookResponse, BookCreate, BookUpdate
from app.schemas.response import ResponseModel
from app.api.deps import get_book_service

router = APIRouter()

# GET lấy danh sách BOOK
@router.get(
    "/",
    response_model=ResponseModel[List[BookResponse]],
    summary="Lấy danh sách sách",
    description="Lấy danh sách sách"
)
async def get_books(service: BookService = Depends(get_book_service)):
    books = await service.get_all_books()
    return ResponseModel(data=books, message="Lấy danh sách thành công")


# POST Tạo sách mới
@router.post(
    "/",
    response_model=ResponseModel[BookResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Tạo sách mới",
    description="Tạo sách mới với category_id và danh sách author_ids"
)
async def create_book(book_data: BookCreate, service: BookService = Depends(get_book_service)):
    new_book = await service.create_new_book(book_data)
    return ResponseModel(data=new_book, message="Thêm sách mới thành công")


# GET xem chi tiết sách theo id
@router.get(
    "/{book_id}",
    response_model=ResponseModel[BookResponse],
    summary="Lấy chi tiết sách",
    description="Lấy thông tin chi tiết 1 cuốn sách theo ID"
)
async def get_book_detail(book_id: str, service: BookService = Depends(get_book_service)):
    book = await service.get_book_detail(book_id)
    return ResponseModel(data=book, message="Lấy thông tin book thành công")


# PUT update sách
@router.put(
    "/{book_id}",
    response_model=ResponseModel[BookResponse],
    summary="Update sách",
    description="Update thông tin sách (có thể update 1 hoặc nhiều field)"
)
async def update_book(
        book_id: str,
        book_data: BookUpdate,
        service: BookService = Depends(get_book_service),
):
    updated_book = await service.update_book(book_id, book_data)
    return ResponseModel(data=updated_book, message="Cập nhật book thành công")


# DELETE xóa book
@router.delete(
    "/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Xóa sách",
    description="Xóa sách khỏi database"
)
async def delete_book(book_id: str, service: BookService = Depends(get_book_service)):
    deleted_book = await service.delete_book(book_id)
    if not deleted_book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sách không tồn tại"
        )

