from fastapi import HTTPException, status
from app.repositories.category_repository import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from typing import List, Optional


class CategoryService:
    def __init__(self, category_repo: CategoryRepository):
        self.category_repo = category_repo


    # hàm map ObjectId sang str
    def _map_id(self, category_dict: dict) -> dict:
        if "_id" in category_dict:
            category_dict["id"] = str(category_dict.pop("_id"))
        return category_dict


    # Logic lấy ds category
    async def get_all_categories(self) -> List[CategoryResponse]:
        categories_list_dict = await self.category_repo.get_all_category()

        categories = []
        for category_dict in categories_list_dict:
            mapped_category = self._map_id(category_dict)
            category_response = CategoryResponse(**mapped_category)
            categories.append(category_response)

        return categories


    # Logic thêm category
    async def create_category(self, category_create: CategoryCreate) -> CategoryResponse:
        existing_category = await self.category_repo.get_category_by_name(category_create.name)
        if existing_category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category '{category_create.name}' đã tồn tại"
            )
        new_category_dict = await self.category_repo.create_category(category_create)
        mapped_category = self._map_id(new_category_dict)

        return CategoryResponse(**mapped_category)


    # Logic lấy category theo id
    async def get_category(self, category_id: str) -> Optional[CategoryResponse]:
        category_dict = await self.category_repo.get_by_category_id(category_id)
        if not category_dict:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category không tồn tại"
            )
        mapped_category = self._map_id(category_dict)
        return CategoryResponse(**mapped_category)


    # Logic sửa category
    async def update_category(self, category_id: str, category_update: CategoryUpdate) -> Optional[CategoryResponse]:
        existing_category = await self.get_category(category_id)
        if not existing_category:
            return None
        updated_category_dict = await self.category_repo.update_category(category_id, category_update)
        mapped_category = self._map_id(updated_category_dict)

        return CategoryResponse(**mapped_category)


    # Logic xóa category
    async def delete_category(self, category_id: str) -> bool:
        deleted = await self.category_repo.delete(category_id)
        return deleted