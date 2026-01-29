from datetime import datetime
from typing import Optional, List, Dict, Any

from bson import ObjectId
from fastapi import HTTPException

from app.exceptions.post import ForbiddenError
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

        # 1️⃣ Xác định người nhắn ở cuộc trò chuyện
        partner_ids = []
        for conv in conversations:
            p1 = conv["participants"][0]["user_id"]
            p2 = conv["participants"][1]["user_id"]

            if p1 == ObjectId(user_id):
                partner_id = p2
            else:
                partner_id = p1
            partner_ids.append(partner_id)

        # 2️⃣ Lấy profile của người đó
        profiles = await self.user_profile_repo.get_public_by_ids(partner_ids)
        profile_map = {profile["user_id"]: profile for profile in profiles}

        # 3️⃣ Gom avatar từ danh sách profile
        avatar_ids = []
        for profile in profiles:
            avatar = profile.get("avatar", [])
            if avatar:
                avatar_ids.append(avatar)

        media_map = {}
        if avatar_ids:
            medias = await self.media_repo.get_by_ids(avatar_ids)
            media_map = {media["_id"]: media for media in medias }

        # 4️⃣ Build response trả về cho client
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


    # Thêm cuộc trò chuyện mới =========================================================================================
    async def _create_private_conversation(
            self,
            user_id: str,
            target_user_id: str
    ) -> ConversationResponse:

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


    # Tìm và thêm ======================================================================================================
    async def find_or_create_private_conversation(
            self,
            user_id: str,
            target_user_id: str
    ) -> ConversationResponse:

        conversation = await self._get_existing_private_conversation(
            user_id, target_user_id
        )

        if conversation:
            return conversation

        return await self._create_private_conversation(
            user_id, target_user_id
        )

    # async def find_or_create_private_conversation(self, user_id: str, target_user_id: str) -> ConversationResponse:
    #     print(f"đi vào đây")
    #     existing_conversation_doc = await self.conversation_repo.find_by_participants([user_id, target_user_id])
    #
    #     if existing_conversation_doc:
    #         participants = existing_conversation_doc["participants"]
    #
    #         # 1️⃣ Gom toàn bộ user_id
    #         user_ids = [(p["user_id"]) for p in participants]
    #
    #         # 2️⃣ Lấy toàn bộ profile 1 lần
    #         profiles = await self.user_profile_repo.get_public_by_ids(user_ids)
    #         profile_map = {
    #             str(profile["user_id"]): profile
    #             for profile in profiles
    #         }
    #
    #         # 3️⃣ Gom toàn bộ avatar_id (nếu có)
    #         avatar_ids = [
    #             profile["avatar"]
    #             for profile in profiles
    #             if profile.get("avatar")
    #         ]
    #
    #         # 4️⃣ Lấy toàn bộ media 1 lần
    #         media_map = {}
    #         if avatar_ids:
    #             medias = await self.media_repo.get_by_ids(avatar_ids)
    #             media_map = {
    #                 str(media["_id"]): media
    #                 for media in medias
    #             }
    #
    #         # 5️⃣ Build response (KHÔNG query DB trong loop)
    #         participants_response = []
    #
    #         for p in participants:
    #             uid = str(p["user_id"])
    #             profile = profile_map.get(uid)
    #
    #             avatar_url = ""
    #             if profile and profile.get("avatar"):
    #                 media = media_map.get(str(profile["avatar"]))
    #                 avatar_url = media.get("url", "") if media else ""
    #
    #             participants_response.append(
    #                 ParticipantEmbedded(
    #                     user_id=uid,
    #                     name=profile.get("display_name", "Người dùng") if profile else "Người dùng",
    #                     avatar=avatar_url,
    #                     joined_at=p["joined_at"]
    #                 )
    #             )
    #
    #         return ConversationResponse(
    #             _id=existing_conversation_doc["_id"],
    #             participants=participants_response,
    #             is_group=existing_conversation_doc["is_group"],
    #             created_at=existing_conversation_doc["created_at"],
    #             updated_at=existing_conversation_doc.get("updated_at")
    #         )
    #
    #     # 2. Nếu chưa, lấy thông tin chi tiết của cả hai người dùng để tạo đối tượng participant
    #
    #     user_profile_doc = await self.user_profile_repo.get_by_user_id(user_id)
    #     target_user_profile_doc = await self.user_profile_repo.get_by_user_id(target_user_id)
    #
    #     user_avatar_url = ""
    #     target_avatar_url = ""
    #
    #     if user_profile_doc.get("avatar", []):
    #         media = await self.media_repo.get_by_id(user_profile_doc["avatar"])
    #         user_avatar_url = media.get("url", "") if media else ""
    #
    #     if target_user_profile_doc.get("avatar", []):
    #         media = await self.media_repo.get_by_id(target_user_profile_doc["avatar"])
    #         target_avatar_url = media.get("url", "") if media else ""
    #
    #
    #     # 4. Tạo cuộc trò chuyện mới với dữ liệu participant đầy đủ
    #     new_conversation_data = {
    #         "participants": [
    #             {
    #                 "user_id": ObjectId(user_id),
    #                 "joined_at": datetime.utcnow()
    #             },
    #             {
    #                 "user_id": ObjectId(target_user_id),
    #                 "joined_at": datetime.utcnow()
    #             }
    #         ],
    #         "is_group": False,
    #         "created_at": datetime.utcnow(),
    #         "updated_at": datetime.utcnow()
    #     }
    #
    #     created_conversation_doc = await self.conversation_repo.create(new_conversation_data)
    #
    #     participants_response = [
    #         ParticipantEmbedded(
    #             user_id=user_id,
    #             name=user_profile_doc.get("display_name", "Người dùng"),
    #             avatar=user_avatar_url,
    #             joined_at=created_conversation_doc["participants"][0]["joined_at"]
    #         ),
    #         ParticipantEmbedded(
    #             user_id=target_user_id,
    #             name=target_user_profile_doc.get("display_name", "Người dùng"),
    #             avatar=target_avatar_url,
    #             joined_at=created_conversation_doc["participants"][1]["joined_at"]
    #         )
    #     ]
    #
    #     return ConversationResponse(
    #         _id=created_conversation_doc["_id"],
    #         participants=participants_response,
    #         is_group=created_conversation_doc["is_group"],
    #         created_at=created_conversation_doc["created_at"],
    #         updated_at=created_conversation_doc["updated_at"]
    #     )

    async def delete_conversation(self, conversation_id: str, user_id: str) -> bool:
        # 1. Lấy thông tin
        conversation = await self.conversation_repo.get_by_id(conversation_id)
        if not conversation:
            return False

        # 2. Check quyền
        is_participant = False
        for p in conversation["participants"]:
            if str(p["user_id"]) == user_id:
                is_participant = True
                break

        if not is_participant:
            raise ForbiddenError()

        # 3. Xóa tin nhắn trước (để đảm bảo sạch sẽ)
        # Lưu ý: Cần inject message_repo vào service này
        await self.message_repo.delete_by_conversation_id(conversation_id)

        # 4. Xóa conversation
        return await self.conversation_repo.delete(conversation_id)