import datetime
from datetime import datetime

from bson import ObjectId
from fastapi import HTTPException, status, UploadFile

from app.core.websocket import manager
from app.repositories.media_repository import MediaRepository
from app.repositories.news_repository import PostRepository
from typing import List, Optional, Dict, Any

from app.repositories.user_profile_repository import UserProfileRepository
from app.repositories.user_repository import UserRepository
from app.schemas.news import PostCreate, PostCreateResponse, MediaPublic, \
    PostsListResponse, UserPublic, PaginatedPostsResponse, PaginationInfo
from app.services.media_service import MediaService


class PostService:
    def __init__(self, post_repo: PostRepository, media_service: MediaService, user_profile_repo: UserProfileRepository, media_repo: MediaRepository):
        self.post_repo = post_repo
        self.media_service = media_service
        self.user_profile_repo = user_profile_repo
        self.media_repo = media_repo

    async def get_all_posts(
            self,
            cursor: Optional[str] = None,  # ← Thêm cursor
            limit: int = 10  # ← Thêm limit
    ) -> PaginatedPostsResponse:  # ← Trả về dict thay vì List

        # 1. Lấy danh sách bài viết (có cursor)
        posts = await self.post_repo.get_all_posts(cursor=cursor, limit=limit + 1)  # +1 để check has_more

        # Check xem còn bài nữa không
        has_more = len(posts) > limit
        if has_more:
            posts = posts[:limit]  # Bỏ bài thừa

        # Tính next_cursor (ID của bài cuối cùng)
        next_cursor = str(posts[-1]["_id"]) if posts else None

        # 2. Gom danh sách id tác giả để query 1 lần
        author_ids = set()
        for p in posts:
            author_ids.add(p["user_id"])

        # 3. Lấy thông tin user và gom id avatar
        users = await self.user_profile_repo.get_public_by_ids(author_ids)
        avatar_ids = {user.get("avatar") for user in users if user.get("avatar")}

        # 4. Lấy thông tin media cho các avatar
        avatars = await self.media_repo.get_by_ids(avatar_ids)
        avatar_map = {str(avatar["_id"]): avatar["url"] for avatar in avatars}


        # 5. Map thông tin user kèm url avatar
        user_map = {}
        for user in users:
            user_id = user["user_id"]
            avatar_id = user.get("avatar")
            public_user = UserPublic(
                id=user_id,
                display_name=user["display_name"],
                avatar=avatar_map.get(str(avatar_id)) if avatar_id else None,
            )
            user_map[user_id] = public_user

        # 6. Gom danh sách id của media trong bài viết
        media_ids = set()
        for post in posts:
            for media in post.get("media_ids", []):
                media_ids.add(media)

        # 5. Lấy thông tin media
        medias = await self.media_repo.get_by_ids(media_ids)

        # 6. Map media
        media_map = {}
        for media in medias:
            media_id = media["_id"]
            public_media = MediaPublic(
                id=media_id,
                type=media["type"],
                url=media["url"]
            )
            media_map[media_id] = public_media

        # 7. Tạo response
        responses = []
        for post in posts:
            author = user_map.get(post["user_id"])

            post_medias = []
            for media_id in post.get("media_ids", []):
                media = media_map.get(media_id)
                if media:
                    post_medias.append(media)

            responses.append(PostsListResponse(
                _id=post["_id"],
                content=post["content"],
                media=post_medias,
                author=author,
                privacy=post["privacy"],
                created_at=post["created_at"]
            ))

        # 8. Trả về kèm pagination info
        return PaginatedPostsResponse(
            data=responses,
            pagination=PaginationInfo(
                next_cursor=next_cursor,
                has_more=has_more,
                limit=limit
            )
        )

    # async def get_all_posts(self) -> List[PostsListResponse]:
    #     #1. Lấy danh sách bài viết để lấy danh sách id của tác giả, id của media
    #     posts =await self.post_repo.get_all_posts()
    #
    #     # 2. Gom danh sách id tác giả để query 1 lần
    #     author_ids = set()
    #     for p in posts:
    #         author_ids.add(p["user_id"])
    #     print(f"Danh sách tác giả: {len(author_ids)}")
    #
    #     # 3. lấy thông tin cần thiết user từ danh sách id tác giả
    #     users = await self.user_profile_repo.get_public_by_ids(author_ids)
    #     print(f"Danh sách user: {len(users)}")
    #
    #     user_map = {}
    #     for user in users:
    #         user_id = user["user_id"]
    #         public_user = UserPublic(
    #                                              id=user_id,
    #                                               display_name=user["display_name"],
    #                                              avatar=user.get("avatar"),
    #                                             )
    #         user_map[user_id] = public_user
    #
    #     #4. gom danh sách id của media nếu có để query 1 lần
    #     media_ids = set()
    #     for post in posts:
    #         for media in post.get("media_ids", []):
    #             media_ids.add(media)
    #
    #     print(f"Danh sách id: {len(media_ids)}")
    #
    #     # 5 lấy thông tin cần thiết của media từ danh sách id media lưu trong bảng post
    #     medias = await self.media_repo.get_by_ids(media_ids)
    #     print(f"Thông tin media: {medias}")
    #
    #     # 7 map theo schema
    #     media_map = {}
    #     for media in medias:
    #         media_id = media["_id"]
    #         public_media = MediaPublic(id=media_id, type=media["type"], url=media["url"])
    #         media_map[media_id] = public_media
    #
    #     responses = []
    #     for post in posts:
    #         author = user_map.get(post["user_id"])
    #
    #         post_medias = []
    #         for media_id in post.get("media_ids", []):
    #             media = media_map.get(media_id)
    #             if media:
    #                 post_medias.append(media)
    #         responses.append(PostsListResponse(
    #             _id=post["_id"],
    #             content=post["content"],
    #             media=post_medias,
    #             author=author,
    #             privacy=post["privacy"],
    #             created_at=post["created_at"]
    #         ))
    #
    #     return responses











    async def create_post(
            self,
            post_data: PostCreate,
            files: Optional[List[UploadFile]],
            user_id: str
    ) -> PostCreateResponse:

        post_dict = post_data.model_dump()

        medias = []

        # Upload media nếu có
        if files:
            medias = await self.media_service.upload_many_media_and_save(
                files=files,
                folder="posts",
            )
            post_dict["media_ids"] = [ObjectId(m.id) for m in medias]
        else:
            post_dict["media_ids"] = []

        # Add fields hệ thống
        post_dict.update({
            "user_id": ObjectId(user_id),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "deleted_at": None
        })

        # Save post
        post = await self.post_repo.create(post_dict)

        media_public = [
            MediaPublic(
                id=m.id,
                type=m.type,
                url=m.url,
            )
            for m in medias
        ]

        # Trả response
        return PostCreateResponse(
            _id=post["_id"],
            content=post["content"],
            privacy=post["privacy"],
            media=media_public,
            created_at=post["created_at"]
        )




