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
from app.services.notification_service import NotificationService


class CommentService:
    def __init__(self,
        comment_repo: CommentRepository, post_repo: PostRepository,
        user_profile_repo: UserProfileRepository, media_repo: MediaRepository,
        notification_service: NotificationService
    ):
        self.comment_repo = comment_repo
        self.post_repo = post_repo
        self.user_profile_repo = user_profile_repo
        self.media_repo = media_repo
        self.notification_service = notification_service


    # Logic gửi bình luận cả rep =======================================================================================
    async def create_comment(self, user_id: str, data: CommentCreate) -> CommentResponse:

        post = await self.post_repo.get_by_id(data.post_id)
        if not post:
            raise NotFoundError()

        comment_dict = {
            "post_id": ObjectId(data.post_id),
            "user_id": ObjectId(user_id),
            "content": data.content,
            "has_replies": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        # Tạo biến xử lí cho Phản hồi tin nhắn
        root_id_obj = None
        reply_to_comment_id_obj = None
        reply_to_user_id_obj = None
        parent_comment = None

        if data.reply_to_comment_id:
            # lấy comment đang rep
            parent_comment = await self.comment_repo.get_by_id(data.reply_to_comment_id)
            if not parent_comment:
                raise NotFoundError()

            reply_to_comment_id_obj = ObjectId(data.reply_to_comment_id)

            # nếu comment rep có root _id
            if parent_comment.get("root_id"):
                root_id_obj = parent_comment["root_id"]
            else:
                root_id_obj = parent_comment["_id"]

            # Lấy user bị reply
            reply_to_user_id_obj = parent_comment.get("user_id")
            
            await self.comment_repo.set_has_replies(root_id_obj, True)
        
        comment_dict["root_id"] = root_id_obj
        comment_dict["reply_to_comment_id"] = reply_to_comment_id_obj
        comment_dict["reply_to_user_id"] = reply_to_user_id_obj

        new_comment = await self.comment_repo.create(comment_dict) # Lưu comment vào DB
        await self.post_repo.increase_comment_count(data.post_id) # cập nhật số bình luận
        
        author_profile = await self.user_profile_repo.get_by_user_id(user_id)
        
        avatar_url = None
        if author_profile and author_profile.get("avatar"):
            avatar_media = await self.media_repo.get_by_id(author_profile["avatar"])
            if avatar_media:
                url = avatar_media["url"]
                if url and not url.startswith("http"):
                     url = f"{settings.SERVER_BASE_URL}/{url.lstrip('/')}"
                avatar_url = url

        author_public = UserPublic(
            id=str(user_id),
            display_name=author_profile["display_name"] if author_profile else "Unknown",
            avatar=avatar_url
        )

        # Gửi thông báo reatime
        current_user_id = user_id
        
        if data.reply_to_comment_id: # nếu đang rep bình luận
            if str(reply_to_user_id_obj) != current_user_id:
                await self.notification_service.create_and_send_notification(
                    recipient_id=str(reply_to_user_id_obj),
                    actor=author_public,
                    type="NEW_REPLY",
                    message=f"đã trả lời bình luận của bạn.",
                    entity_ref={
                        "post_id": data.post_id,
                        "comment_id": str(new_comment['_id']),
                        "root_id": str(root_id_obj),
                    }
                )
        else: # nếu là bình luận gốc
            if str(post.get("user_id")) != current_user_id:
                await self.notification_service.create_and_send_notification(
                    recipient_id=str(post.get("user_id")),
                    actor=author_public,
                    type="NEW_COMMENT",
                    message=f" đã bình luận về bài viết của bạn.",
                    entity_ref={
                        "post_id": str(data.post_id),
                        "comment_id": str(new_comment['_id']),
                    }
                )

        return CommentResponse(
            _id=str(new_comment["_id"]),
            post_id=str(new_comment["post_id"]),
            root_id=str(new_comment["root_id"]) if new_comment.get("root_id") else None,
            reply_to_comment_id=str(new_comment["reply_to_comment_id"]) if new_comment.get("reply_to_comment_id") else None,
            reply_to_user_id=str(new_comment["reply_to_user_id"]) if new_comment.get("reply_to_user_id") else None,
            content=new_comment["content"],
            has_replies=new_comment.get("has_replies", False),
            author=author_public,
            created_at=new_comment["created_at"]
        )


    # Lấy tất cả bình luận trong bài viết ==============================================================================
    async def get_root_comments_for_post(self, post_id: str, limit: int = 10, cursor: Optional[str] = None) -> List[CommentResponse]:
        comments = await self.comment_repo.get_root_comments(post_id, limit, cursor)
        
        if not comments:
            return []

        # Lấy thông tin người nhắn
        user_ids = [c["user_id"] for c in comments]
        users = await self.user_profile_repo.get_public_by_ids(user_ids)
        
        # Lấy avatars
        avatar_ids = [user.get("avatar") for user in users if user.get("avatar")]
        avatars = await self.media_repo.get_by_ids(avatar_ids) if avatar_ids else []
        
        avatar_map = {}
        for avatar in avatars:
             url = avatar["url"]
             if url and not url.startswith("http"):
                 url = f"{settings.SERVER_BASE_URL}/{url.lstrip('/')}"
             avatar_map[str(avatar["_id"])] = url

        user_map = {}
        for user in users:
            uid = user["user_id"]
            avatar_id = user.get("avatar")
            user_map[uid] = UserPublic(
                id=str(uid),
                display_name=user.get("display_name", "Unknown"),
                avatar=avatar_map.get(str(avatar_id))
            )

        # Tạo reponse trả về
        response = []
        for c in comments:
            author = user_map.get(c["user_id"])
            if not author:
                author = UserPublic(id=str(c["user_id"]), display_name="Unknown", avatar=None)

            response.append(CommentResponse(
                _id=str(c["_id"]),
                post_id=str(c["post_id"]),
                root_id=str(c["root_id"]) if c.get("root_id") else None,
                reply_to_comment_id=str(c["reply_to_comment_id"]) if c.get("reply_to_comment_id") else None,
                reply_to_user_id=str(c["reply_to_user_id"]) if c.get("reply_to_user_id") else None,
                content=c["content"],
                has_replies=c.get("has_replies", False),
                author=author,
                created_at=c["created_at"]
            ))
            
        return response

    async def get_replies_for_comment_thread(self, root_comment_id: str, limit: int = 10, cursor: Optional[str] = None) -> List[CommentResponse]:
        replies = await self.comment_repo.get_replies(root_comment_id, limit, cursor)

        if not replies:
            return []

        # Lấy thông tin người nhắn (Reusable block)
        user_ids = [r["user_id"] for r in replies]
        users = await self.user_profile_repo.get_public_by_ids(user_ids)

        # Lấy avatars (Reusable block)
        avatar_ids = [user.get("avatar") for user in users if user.get("avatar")]
        avatars = await self.media_repo.get_by_ids(avatar_ids) if avatar_ids else []

        avatar_map = {}
        for avatar in avatars:
             url = avatar["url"]
             if url and not url.startswith("http"):
                 url = f"{settings.SERVER_BASE_URL}/{url.lstrip('/')}"
             avatar_map[str(avatar["_id"])] = url

        user_map = {}
        for user in users:
            uid = user["user_id"]
            avatar_id = user.get("avatar")
            user_map[uid] = UserPublic(
                id=str(uid),
                display_name=user.get("display_name", "Unknown"),
                avatar=avatar_map.get(str(avatar_id))
            )

        # Tạo reponse trả về
        response = []
        for r in replies:
            author = user_map.get(r["user_id"])
            if not author:
                author = UserPublic(id=str(r["user_id"]), display_name="Unknown", avatar=None)

            response.append(CommentResponse(
                _id=str(r["_id"]),
                post_id=str(r["post_id"]),
                root_id=str(r["root_id"]) if r.get("root_id") else None,
                reply_to_comment_id=str(r["reply_to_comment_id"]) if r.get("reply_to_comment_id") else None,
                reply_to_user_id=str(r["reply_to_user_id"]) if r.get("reply_to_user_id") else None,
                content=r["content"],
                has_replies=r.get("has_replies", False),
                author=author,
                created_at=r["created_at"]
            ))

        return response




