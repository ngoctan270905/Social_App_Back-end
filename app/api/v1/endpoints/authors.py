from fastapi import APIRouter, status, Depends, HTTPException
from typing import List
from app.schemas.response import ResponseModel
from app.services.author_service import AuthorService
from app.schemas.author import AuthorCreate, AuthorUpdate, AuthorResponse
from app.api.deps import get_author_service

router = APIRouter()

# GET lấy danh sách authors
@router.get(
    "/",
    response_model=ResponseModel[List[AuthorResponse]],
    summary="Lấy danh sách tất cả tác giả"
)
async def get_authors(service: AuthorService = Depends(get_author_service)):
    authors = await service.get_all_authors()
    return ResponseModel(data=authors, message="Lấy danh sách tác giả thành công")


# POST thêm author mới
@router.post(
    "/",
    response_model=ResponseModel[AuthorResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Tạo author mới"
)
async def create_author(author_data: AuthorCreate, service: AuthorService = Depends(get_author_service)):
    new_author = await service.create_author(author_data)
    return ResponseModel(data=new_author, message="Thêm tác giả thành công")


# GET lấy chi tiết tác giả
@router.get(
    "/{author_id}",
    response_model=ResponseModel[AuthorResponse],
    summary="Lấy chi tiết tác giả"
)
# Lấy chi tiết tác giả theo ID
async def get_author(author_id: str, service: AuthorService = Depends(get_author_service)):
   author = await service.get_author(author_id)
   if not author:
       raise HTTPException(status_code=404, detail="Author not found")
   return ResponseModel(data=author, message="Lấy thông tin thành công")


# PUT update tác giả
@router.put(
    "/{author_id}",
    response_model=ResponseModel[AuthorResponse],
    summary="Cập nhật author"
)
async def update_author(
    author_id: str,
    author_data: AuthorUpdate,
    service: AuthorService = Depends(get_author_service)
):
    updated_author = await service.update_author(author_id, author_data)
    if not updated_author:
        raise HTTPException(status_code=404, detail="Author not found")
    return ResponseModel(data=updated_author, message="Cập nhật author thành công")



@router.delete(
    "/{author_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Xóa author"
)
async def delete_author(author_id: str, service: AuthorService = Depends(get_author_service)):
   deleted_author = await service.delete_author(author_id)
   if not deleted_author:
       raise HTTPException(status_code=404, detail="Author not found")
