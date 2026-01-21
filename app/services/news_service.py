import datetime
from datetime import datetime
from bson import ObjectId
from fastapi import UploadFile
from typing import List, Optional, Dict, Any

from app.exceptions.post import NotFoundError, ForbiddenError

from app.repositories.media_repository import MediaRepository
from app.repositories.posts_repository import PostRepository
from app.repositories.user_profile_repository import UserProfileRepository

from app.schemas.posts import PostCreate, PostCreateResponse, MediaPublic, \
    PostsListResponse, UserPublic, PaginatedPostsResponse, PaginationInfo, PostDetailResponse, PostUpdate

from app.services.media_service import MediaService


class PostService:
    def __init__(self, post_repo: PostRepository,
                       media_service: MediaService,
                       user_profile_repo: UserProfileRepository,
                       media_repo: MediaRepository):

        self.post_repo = post_repo
        self.media_service = media_service
        self.user_profile_repo = user_profile_repo
        self.media_repo = media_repo


    # Logic lấy danh sách bài viết và phân trang =======================================================================
    async def get_all_posts(
            self,
            cursor: Optional[str] = None,
            limit: int = 5
    ) -> PaginatedPostsResponse:

        #1. Lấy danh sách bài viết
        posts = await self.post_repo.get_all_posts(cursor=cursor, limit=limit + 1)

        # Check xem còn bài nữa không
        has_more = len(posts) > limit
        if has_more:
            posts = posts[:limit]

        next_cursor = str(posts[-1]["_id"]) if posts else None

        # 2. Gom danh sách id tác giả để query 1 lần
        author_ids = set()
        for p in posts:
            author_ids.add(p["user_id"])

        # 3. Lấy thông tin user và gom id avatar
        users = await self.user_profile_repo.get_public_by_ids(author_ids)
        avatar_ids = [user.get("avatar") for user in users if user.get("avatar")]

        # 4. Lấy thông tin media cho các avatar
        avatars = await self.media_repo.get_by_ids(avatar_ids)
        # avatar_map = {str(avatar["_id"]): avatar["url"] for avatar in avatars}
        avatar_map = {}
        for avatar in avatars:
            key = str(avatar["_id"])
            value = avatar["url"]
            avatar_map[key] = value

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
        media_ids = []
        for post in posts:
            for media in post.get("media_ids", []):
                media_ids.append(media)

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


    # Logic xem chi tiết 1 bài viết ====================================================================================
    async def get_detail_post(self, post_id: str) -> PostDetailResponse:

        #1. Lấy bài viết
        post = await self.post_repo.get_by_id(post_id)
        if not post:
            raise NotFoundError()

        #2. Lấy thông tin của tác giả
        author = await self.user_profile_repo.get_by_user_id(post["user_id"])

        # 3. Lấy avatar
        avatar_url = None
        avatar_id = author.get("avatar")
        if avatar_id:
            avatar_media = await self.media_repo.get_by_id(avatar_id)
            if avatar_media:
                avatar_url = avatar_media["url"]

        #4. Lấy thông tin author
        author = UserPublic(id=author["user_id"], display_name=author["display_name"], avatar=avatar_url)

        #5 Lấy media của bài viết
        media_items = []
        media_ids = post.get("media_ids", [])
        if media_ids:
            medias = await self.media_repo.get_by_ids(media_ids)
            if medias:
                for media in medias:
                    media_items.append(MediaPublic(id=media["_id"], type=media["type"], url=media["url"]))

        return PostDetailResponse(
            _id=post["_id"],
            content=post.get("content"),
            media=media_items,
            author=author,
            privacy=post["privacy"],
            created_at=post["created_at"],
        )


    # Logic thêm bài viết mới ==========================================================================================
    async def create_post(self,
                          post_data: PostCreate,
                          files: Optional[List[UploadFile]],
                          user_id: str
    ) -> PostCreateResponse:

        #1. Map từ Pydantic object sang dict
        post_dict = post_data.model_dump()

        medias = []

        # Upload media nếu có
        if files:
            medias = await self.media_service.upload_many_media_and_save(files=files,folder="posts")
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
            MediaPublic(id=m.id,type=m.type,url=m.url,)
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


    # Logic update post ================================================================================================
    async def update_post(
            self,
            post_id: str,
            user_id: str,
            content: Optional[str] = None,
            privacy: Optional[str] = None,
            keep_media_ids: List[str] = [],  # Danh sách ID ảnh cũ muốn giữ lại
            new_files: List[UploadFile] = []  # Danh sách ảnh mới muốn thêm
    ) -> PostCreateResponse:

        # 1. Lấy thông tin bài viết hiện tại
        post = await self.post_repo.get_by_id(post_id)
        if not post:
            raise NotFoundError()

        # 2. Check quyền
        if str(post["user_id"]) != user_id:
            raise ForbiddenError()

        # 3. Xử lý Media
        current_media_ids = [str(m) for m in post.get("media_ids", [])]

        final_media_ids = []
        for mid in current_media_ids:
            if mid in keep_media_ids:
                final_media_ids.append(ObjectId(mid))

        # Upload ảnh mới (nếu có)
        if new_files:
            new_medias = await self.media_service.upload_many_media_and_save(
                files=new_files,
                folder="posts",
            )
            for m in new_medias:
                final_media_ids.append(ObjectId(m.id))

        # 4. Chuẩn bị dữ liệu update
        update_data = {
            "updated_at": datetime.utcnow(),
            "media_ids": final_media_ids  # Cập nhật danh sách ID mới
        }

        if content is not None:
            update_data["content"] = content
        if privacy is not None:
            update_data["privacy"] = privacy

        # 5. Thực hiện update
        post = await self.post_repo.update(update_data, post_id)

        # 6. Lấy thông tin media đầy đủ để trả về
        media_public = []
        if final_media_ids:
            medias = await self.media_repo.get_by_ids(final_media_ids)
            media_public = [
                MediaPublic(id=str(m["_id"]),type=m["type"],url=m["url"])
                for m in medias
            ]

        return PostCreateResponse(
            _id=post["_id"],
            content=post["content"],
            privacy=post["privacy"],
            media=media_public,
            created_at=post["created_at"]
        )

    # Logic delete post ================================================================================================
    async def delete_post(self, post_id: str, user_id: str) -> bool:

        post = await self.post_repo.get_by_id(post_id)
        if not post:
            raise NotFoundError()

        if str(post["user_id"]) != str(user_id):
            raise ForbiddenError()

        media_ids = post.get("media_ids", [])
        if media_ids:
            medias = await self.media_repo.get_by_ids(media_ids)
            delete_media = await self.media_repo.delete_many(media_ids)

        delete_post = await self.post_repo.delete(post_id)
        return True

    async def get_user_posts(
            self,
            user_id: str,
            current_user_id: str,
            cursor: Optional[str] = None,
            limit: int = 5
    ) -> PaginatedPostsResponse:

        # Logic phân quyền riêng tư
        if str(current_user_id) == str(user_id):
            privacy_filter = None  # Chính chủ: Lấy tất cả (Public, Friends, Private)
        else:
            privacy_filter = ["public"]  # Người khác: Chỉ lấy bài Public

        # 1. Lấy danh sách bài viết từ repo
        posts = await self.post_repo.get_posts_by_user(
            user_id=user_id,
            privacy_filter=privacy_filter,
            cursor=cursor,
            limit=limit + 1
        )

        # Check xem còn bài nữa không
        has_more = len(posts) > limit
        if has_more:
            posts = posts[:limit]

        next_cursor = str(posts[-1]["_id"]) if posts else None

        # 2. Gom danh sách id tác giả để query 1 lần
        author_ids = set()
        for p in posts:
            author_ids.add(p["user_id"])

        # 3. Lấy thông tin user và gom id avatar
        users = await self.user_profile_repo.get_public_by_ids(author_ids)
        avatar_ids = [user.get("avatar") for user in users if user.get("avatar")]

        # 4. Lấy thông tin media cho các avatar
        avatars = await self.media_repo.get_by_ids(avatar_ids)
        avatar_map = {}
        for avatar in avatars:
            key = str(avatar["_id"])
            value = avatar["url"]
            avatar_map[key] = value

        # 5. Map thông tin user kèm url avatar
        user_map = {}
        for user in users:
            uid = user["user_id"]
            avatar_id = user.get("avatar")
            public_user = UserPublic(
                id=uid,
                display_name=user["display_name"],
                avatar=avatar_map.get(str(avatar_id)) if avatar_id else None,
            )
            user_map[uid] = public_user

        # 6. Gom danh sách id của media trong bài viết
        media_ids = []
        for post in posts:
            for media in post.get("media_ids", []):
                media_ids.append(media)

        # 7. Lấy thông tin media
        medias = await self.media_repo.get_by_ids(media_ids)

        # 8. Map media
        media_map = {}
        for media in medias:
            media_id = media["_id"]
            public_media = MediaPublic(
                id=media_id,
                type=media["type"],
                url=media["url"]
            )
            media_map[media_id] = public_media

        # 9. Tạo response
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

        # 10. Trả về kèm pagination info
        return PaginatedPostsResponse(
            data=responses,
            pagination=PaginationInfo(
                next_cursor=next_cursor,
                has_more=has_more,
                limit=limit
            )
        )



