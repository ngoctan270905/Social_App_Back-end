from fastapi import HTTPException, status
from typing import List, Optional
from app.repositories.author_repository import AuthorRepository
from app.schemas.author import AuthorCreate, AuthorUpdate, AuthorResponse


class AuthorService:
    def __init__(self, author_repo: AuthorRepository):
        self.author_repo = author_repo

    # logic chuyển ObjectId sang tr
    def map_id(self, author_dict: dict) -> dict:
        if "_id" in author_dict:
            author_dict["id"] = str(author_dict.pop("_id"))
        return author_dict


    # logic lấy all ds authors
    async def get_all_authors(self) -> List[AuthorResponse]:
        author_list_dict = await self.author_repo.get_all()

        authors = []
        for author_dict in author_list_dict:
            mapped_author = self.map_id(author_dict)
            author_response = AuthorResponse(**mapped_author)
            authors.append(author_response)
        return authors


    # logic thêm author mới
    async def create_author(self, author_create: AuthorCreate) -> AuthorResponse:
        existing_author = await self.author_repo.get_author_by_name(author_create.name)
        if existing_author:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Author '{author_create.name}' đã tồn tại"
            )
        new_author_dict = await self.author_repo.create(author_create)
        mapped_author = self.map_id(new_author_dict)
        return AuthorResponse(**mapped_author)


    # logic tìm người dùng theo id
    async def get_author(self, author_id: str) -> Optional[AuthorResponse]:
        author_dict = await self.author_repo.get_by_id(author_id)
        if not author_dict:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Author không tồn tại"
            )
        mapped_author = self.map_id(author_dict)
        return AuthorResponse(**mapped_author)


    # logic update tác giả
    async def update_author(self, author_id: str, author_update: AuthorUpdate) -> Optional[AuthorResponse]:
        existing_author = await self.author_repo.get_by_id(author_id)
        if not existing_author:
            return None
        updated_author_dict = await self.author_repo.update(author_id, author_update)
        mapped_author = self.map_id(updated_author_dict)
        return AuthorResponse(**mapped_author)


    # logic xóa tác giả
    async def delete_author(self, author_id: str) -> bool:
        deleted_author = await self.author_repo.delete(author_id)
        return deleted_author

