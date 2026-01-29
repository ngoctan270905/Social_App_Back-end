from datetime import datetime
from typing import Optional, List, Dict, Any

from bson import ObjectId
from fastapi import HTTPException

from app.exceptions.post import ForbiddenError, NotFoundError
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.media_repository import MediaRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.user_profile_repository import UserProfileRepository
from app.repositories.user_repository import UserRepository
from app.schemas.conversation import ConversationResponse, ParticipantEmbedded, ConversationListItem, ConversationPartner


class ConversationService:
    def __init__(
        self,
        conversation_repo: ConversationRepository,
        user_profile_repo: UserProfileRepository,
        media_repo: MediaRepository,
        message_repo: MessageRepository):
        self.conversation_repo = conversation_repo
        self.user_profile_repo = user_profile_repo
        self.media_repo = media_repo
        self.message_repo = message_repo


    # Lấy danh sách cuộc trò chuyện ====================================================================================
    async def get_conversations_for_user(self, user_id: str) -> List[ConversationListItem]:
        conversations = await self.conversation_repo.get_conversations_for_user(user_id)
        if not conversations:
            return []

        # 1.Xác định người nhắn ở cuộc trò chuyện
        partner_ids = []
        for conv in conversations:
            p1 = conv["participants"][0]["user_id"]
            p2 = conv["participants"][1]["user_id"]

            if p1 == ObjectId(user_id):
                partner_id = p2
            else:
                partner_id = p1
            partner_ids.append(partner_id)

        # 2.Lấy profile của người đó
        profiles = await self.user_profile_repo.get_public_by_ids(partner_ids)
        profile_map = {profile["user_id"]: profile for profile in profiles}

        # 3.Gom avatar từ danh sách profile
        avatar_ids = []
        for profile in profiles:
            avatar = profile.get("avatar", [])
            if avatar:
                avatar_ids.append(avatar)

        media_map = {}
        if avatar_ids:
            medias = await self.media_repo.get_by_ids(avatar_ids)
            media_map = {media["_id"]: media for media in medias }

        # 4.Build response trả về cho client
        result = []

        for conv in conversations:
            p1 = conv["participants"][0]["user_id"]
            p2 = conv["participants"][1]["user_id"]

            if p1 == ObjectId(user_id):
                partner_id = p2
            else:
                partner_id = p1

            profile = profile_map.get(partner_id)

            partner = None
            if profile:
                avatar_url = ""
                avatar_id = profile.get("avatar")

                if avatar_id:
                    media = media_map.get(avatar_id)
                    avatar_url = media.get("url", "") if media else ""

                partner = ConversationPartner(
                    user_id=str(partner_id),
                    name=profile.get("display_name", "Người dùng"),
                    avatar=avatar_url
                )

            result.append(
                ConversationListItem(
                    _id=conv["_id"],
                    is_group=conv.get("is_group", False),
                    partner=partner
                )
            )

        return result


    # Tìm cuộc trò chuyện giữa 2 người =================================================================================
    async def _get_existing_private_conversation(self, user_id: str,target_user_id: str) -> Optional[ConversationResponse]:

        existing_conversation_doc = await self.conversation_repo.find_by_participants([user_id, target_user_id])

        if not existing_conversation_doc:
            return None

        participants = existing_conversation_doc["participants"]

        # ---- Batch profiles
        user_ids = [(p["user_id"]) for p in participants]
        profiles = await self.user_profile_repo.get_public_by_ids(user_ids)

        profile_map = {
            str(profile["user_id"]): profile
            for profile in profiles
        }

        # ---- Batch medias (avatar)
        avatar_ids = [
            profile["avatar"]
            for profile in profiles
            if profile.get("avatar")
        ]

        media_map = {}
        if avatar_ids:
            medias = await self.media_repo.get_by_ids(avatar_ids)
            media_map = {
                str(media["_id"]): media
                for media in medias
            }

        # ---- Build response (lặp thì kệ)
        participants_response = []

        for p in participants:
            uid = str(p["user_id"])
            profile = profile_map.get(uid)

            avatar_url = ""
            if profile and profile.get("avatar"):
                media = media_map.get(str(profile["avatar"]))
                avatar_url = media.get("url", "") if media else ""

            participants_response.append(
                ParticipantEmbedded(
                    user_id=uid,
                    name=profile.get("display_name", "Người dùng") if profile else "Người dùng",
                    avatar=avatar_url,
                    joined_at=p["joined_at"]
                )
            )

        return ConversationResponse(
            _id=existing_conversation_doc["_id"],
            participants=participants_response,
            is_group=existing_conversation_doc["is_group"],
            created_at=existing_conversation_doc["created_at"],
            updated_at=existing_conversation_doc.get("updated_at")
        )


    # Ẩn cuộc trò chuyện ===============================================================================================
    async def hide_conversation_for_user(self, conversation_id: str, user_id: str) -> bool:
        conversation = await self.conversation_repo.get_by_id(conversation_id)
        if not conversation:
            raise NotFoundError()

        is_participant = False

        for participant in conversation.get("participants", []):
            participant_user_id = str(participant["user_id"])

            if participant_user_id == user_id:
                is_participant = True
                break

        if not is_participant:
            raise ForbiddenError()

        return await self.conversation_repo.hide_for_user(conversation_id, user_id)


    # Thêm cuộc trò chuyện mới =========================================================================================
    async def _create_private_conversation(self, user_id: str, target_user_id: str) -> ConversationResponse:

        now = datetime.utcnow()

        new_conversation_data = {
            "participants": [
                {"user_id": ObjectId(user_id), "joined_at": now},
                {"user_id": ObjectId(target_user_id), "joined_at": now}
            ],
            "is_group": False,
            "created_at": now,
            "updated_at": now
        }

        created_conversation_doc = await self.conversation_repo.create(
            new_conversation_data
        )

        participants = created_conversation_doc["participants"]

        # ---- Batch profiles
        user_ids = [(p["user_id"]) for p in participants]
        profiles = await self.user_profile_repo.get_public_by_ids(user_ids)

        profile_map = {
            str(profile["user_id"]): profile
            for profile in profiles
        }

        # ---- Batch medias
        avatar_ids = [
            profile["avatar"]
            for profile in profiles
            if profile.get("avatar")
        ]

        media_map = {}
        if avatar_ids:
            medias = await self.media_repo.get_by_ids(avatar_ids)
            media_map = {
                str(media["_id"]): media
                for media in medias
            }

        # ---- Build response (lặp thì kệ)
        participants_response = []

        for p in participants:
            uid = str(p["user_id"])
            profile = profile_map.get(uid)

            avatar_url = ""
            if profile and profile.get("avatar"):
                media = media_map.get(str(profile["avatar"]))
                avatar_url = media.get("url", "") if media else ""

            participants_response.append(
                ParticipantEmbedded(
                    user_id=uid,
                    name=profile.get("display_name", "Người dùng") if profile else "Người dùng",
                    avatar=avatar_url,
                    joined_at=p["joined_at"]
                )
            )

        return ConversationResponse(
            _id=created_conversation_doc["_id"],
            participants=participants_response,
            is_group=created_conversation_doc["is_group"],
            created_at=created_conversation_doc["created_at"],
            updated_at=created_conversation_doc["updated_at"]
        )


    # Tìm hoặc tạo direct ==============================================================================================
    async def find_or_create_private_conversation(self,user_id: str,target_user_id: str) -> ConversationResponse:

        # 1. Tìm cuộc trò chuyện đã tồn tại
        conversation_doc = await self.conversation_repo.find_direct_conversation_between_users(
            user_id, target_user_id
        )

        # 2. Nếu tìm thấy:
        if conversation_doc:
            conversation_id = str(conversation_doc["_id"])

            # Kiểm tra xem người dùng hiện tại có đang ẩn nó không
            is_hidden = False
            deleted_by_list = conversation_doc.get("deleted_by", [])
            for deleted_item in deleted_by_list:
                deleted_user_id = str(deleted_item["user_id"])
                if deleted_user_id == user_id:
                    is_hidden = True
                    break

            if is_hidden:
                await self.conversation_repo.resurrect_for_user(conversation_id, user_id)

            return await self._get_existing_private_conversation(user_id, target_user_id)

        return await self._create_private_conversation(user_id, target_user_id)

