from datetime import datetime
from typing import Optional, List

from bson import ObjectId
from app.exceptions.post import NotFoundError
from app.repositories.comment_repository import CommentRepository
from app.repositories.posts_repository import PostRepository
from app.repositories.user_profile_repository import UserProfileRepository
from app.repositories.media_repository import MediaRepository
from app.schemas.comment import CommentCreate, CommentResponse
from app.schemas.posts import UserPublic
from app.core.config import settings

class CommentService:
    def __init__(
        self, 
        comment_repo: CommentRepository,
        post_repo: PostRepository,
        user_profile_repo: UserProfileRepository,
        media_repo: MediaRepository
    ):
        self.comment_repo = comment_repo
        self.post_repo = post_repo
        self.user_profile_repo = user_profile_repo
        self.media_repo = media_repo

    # Logic thêm bình luận =============================================================================================
    async def create_comment(self, user_id: str, data: CommentCreate) -> CommentResponse:
        post = await self.post_repo.get_by_id(data.post_id)
        if not post:
            raise NotFoundError()

        # 1. Xử lý parent_id (Nếu là Reply)
        parent_id_obj = None
        if data.parent_id:
             parent_id_obj = ObjectId(data.parent_id)
             # (Optional) Validate parent comment exists here if needed

        # 2. Tạo data comment
        comment_dict = {
            "post_id": ObjectId(data.post_id),
            "user_id": ObjectId(user_id),
            "content": data.content,
            "parent_id": parent_id_obj, # Lưu parent_id
            "reply_count": 0,           # Khởi tạo reply_count
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        # 3. Lưu comment
        new_comment = await self.comment_repo.create(comment_dict)

        # 4. Tăng count comment cho post
        await self.post_repo.increase_comment_count(data.post_id)
        
        # 5. Tăng count reply cho comment cha (Nếu có)
        if data.parent_id:
            await self.comment_repo.increment_reply_count(data.parent_id)

        # 6. Lấy info người comment
        author_profile = await self.user_profile_repo.get_by_user_id(user_id)
        
        avatar_url = None
        if author_profile and author_profile.get("avatar"):
            avatar_media = await self.media_repo.get_by_id(author_profile["avatar"])
            if avatar_media:
                url = avatar_media["url"]
                # Logic xử lý URL local
                if url and not url.startswith("http"):
                     url = f"{settings.SERVER_BASE_URL}/{url.lstrip('/')}"
                avatar_url = url

        author_public = UserPublic(
            id=str(user_id),
            display_name=author_profile["display_name"] if author_profile else "Unknown",
            avatar=avatar_url
        )

        return CommentResponse(
            _id=new_comment["_id"],
            post_id=str(new_comment["post_id"]),
            parent_id=str(new_comment["parent_id"]) if new_comment.get("parent_id") else None,
            content=new_comment["content"],
            author=author_public,
            created_at=new_comment["created_at"],
            reply_count=new_comment.get("reply_count", 0)
        )


    # Lấy tất cả bình luận trong bài viết ==============================================================================
    async def get_comments_by_post(self, post_id: str, limit: int = 10, cursor: Optional[str] = None) -> List[CommentResponse]:
        comments = await self.comment_repo.get_by_post_id(post_id, limit, cursor)
        
        if not comments:
            return []

        # Lấy thông tin người nhắn
        user_ids = []
        for user in comments:
            user_ids.append(user["user_id"])

        # Lấy thông tin của tất cả user
        users = await self.user_profile_repo.get_public_by_ids(user_ids)
        
        # Lấy avatars
        avatar_ids = []
        for avatar_user in users:
            avatar = avatar_user.get("avatar", [])
            if avatar:
                avatar_ids.append(avatar)
        avatars = await self.media_repo.get_by_ids(avatar_ids)

        # map key: value cho avatar
        avatar_map = {}
        for avatar in avatars:
             url = avatar["url"]
             if url and not url.startswith("http"):
                 url = f"{settings.SERVER_BASE_URL}/{url.lstrip('/')}"
             avatar_map[str(avatar["_id"])] = url

        # map sang User Public
        user_map = {}
        for user in users:
            uid = user["user_id"]
            avatar_id = user.get("avatar")
            user_map[uid] = UserPublic(
                id=uid,
                display_name=user["display_name"],
                avatar=avatar_map.get(str(avatar_id))
            )

        # Tạo reponse trả về
        response = []
        for c in comments:
            author = user_map.get(c["user_id"], [])
            response.append(CommentResponse(
                _id=c["_id"],
                post_id=str(c["post_id"]),
                parent_id=str(c["parent_id"]) if c.get("parent_id") else None,
                content=c["content"],
                author=author,
                created_at=c["created_at"],
                reply_count=c.get("reply_count", 0)
            ))

            
        return response

    async def get_replies_by_comment(self, comment_id: str, limit: int = 10, cursor: Optional[str] = None) -> List[
        CommentResponse]:

        replies = await self.comment_repo.get_replies(comment_id, limit, cursor)

        if not replies:
            return []

        # Lấy thông tin người nhắn

        user_ids = []

        for user in replies:
            user_ids.append(user["user_id"])

        # Lấy thông tin của tất cả user

        users = await self.user_profile_repo.get_public_by_ids(user_ids)

        # Lấy avatars

        avatar_ids = []

        for avatar_user in users:

            avatar = avatar_user.get("avatar", [])

            if avatar:
                avatar_ids.append(avatar)

        avatars = await self.media_repo.get_by_ids(avatar_ids)

        # map key: value cho avatar

        avatar_map = {}

        for avatar in avatars:

            url = avatar["url"]

            if url and not url.startswith("http"):
                url = f"{settings.SERVER_BASE_URL}/{url.lstrip('/')}"

            avatar_map[str(avatar["_id"])] = url

        # map sang User Public

        user_map = {}

        for user in users:
            uid = user["user_id"]

            avatar_id = user.get("avatar")

            user_map[uid] = UserPublic(

                id=uid,

                display_name=user["display_name"],

                avatar=avatar_map.get(str(avatar_id))

            )

        # Tạo reponse trả về

        response = []

        for r in replies:
            author = user_map.get(r["user_id"], [])

            response.append(CommentResponse(

                _id=r["_id"],

                post_id=str(r["post_id"]),

                parent_id=str(r["parent_id"]) if r.get("parent_id") else None,

                content=r["content"],

                author=author,

                created_at=r["created_at"],

                reply_count=r.get("reply_count", 0)

            ))

        return response




