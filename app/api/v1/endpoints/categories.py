from fastapi import APIRouter, Depends, status, HTTPException
from typing import List
from app.schemas.response import ResponseModel
from app.services.category_service import CategoryService
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from app.api.deps import get_category_service

router = APIRouter()

# GET lấy ds tất cả categories
@router.get(
    "/",
    response_model=ResponseModel[List[CategoryResponse]],
    summary="Lấy danh sách categories"
)
async def get_categories(service: CategoryService = Depends(get_category_service)):
    categories = await service.get_all_categories()
    return ResponseModel(data=categories, message="Lấy danh sách category thành công")


# POST tạo category mới
@router.post(
    "/",
    response_model=ResponseModel[CategoryResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Tạo category mới"
)
async def create_category(
    category_data: CategoryCreate,
    service: CategoryService = Depends(get_category_service)
):
    new_category = await service.create_category(category_data)
    return ResponseModel(data=new_category, message="Thêm category thành công")


# GET category theo ID:
@router.get(
    "/{category_id}",
    response_model=ResponseModel[CategoryResponse],
    summary="Lấy chi tiết category"
)
async def get_category(
    category_id: str,
    service: CategoryService = Depends(get_category_service)
):
    category = await service.get_category(category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return ResponseModel(data=category, message="Lấy thông tin danh mục thành công")


# PUT update category:
@router.put(
    "/{category_id}",
    response_model=ResponseModel[CategoryResponse],
    summary="Cập nhật category"
)
async def update_category(
    category_id: str,
    category_data: CategoryUpdate,
    service: CategoryService = Depends(get_category_service)
):
    updated_category = await service.update_category(category_id, category_data)
    if not updated_category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return ResponseModel(data=updated_category, message="Cập nhật danh mục thành công")


# DELETE category
@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Xóa category"
)
async def delete_category(
    category_id: str,
    service: CategoryService = Depends(get_category_service)
):

    deleted = await service.delete_category(category_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")