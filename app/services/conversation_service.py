from datetime import datetime
from typing import Optional, List, Dict, Any

from bson import ObjectId

from app.repositories.conversation_repository import ConversationRepository
from app.repositories.media_repository import MediaRepository
from app.repositories.user_profile_repository import UserProfileRepository
from app.repositories.user_repository import UserRepository
from app.schemas.conversation import ConversationResponse, ParticipantEmbedded


class ConversationService:
    def __init__(
        self,
        conversation_repo: ConversationRepository,
        user_profile_repo: UserProfileRepository,
        media_repo: MediaRepository,):
        self.conversation_repo = conversation_repo
        self.user_profile_repo = user_profile_repo
        self.media_repo = media_repo


    # Tìm kiếm hoặc thêm cuộc trò truyện ===============================================================================
    async def get_or_create_private_conversation(self, sender_id: str, target_user_id: str) -> str:
        existing_conv = await self.conversation_repo.find_direct_conversation_between_users(sender_id, target_user_id)
        if existing_conv:
            return str(existing_conv["_id"])

        # Tạo mới
        new_conv = await self.conversation_repo.create(user_ids=[sender_id, target_user_id], is_group=False)
        return str(new_conv["_id"])


    # Lấy danh sách chat của người dùng ================================================================================
    # async def get_conversations_for_user(self, user_id: str) -> List[Dict[str, Any]]:
    #     conversations = await self.conversation_repo.get_conversations_for_user(user_id)
    #     return conversations

    async def get_conversations_for_user(
            self,
            user_id: str
    ) -> List[Dict[str, Any]]:

        conversations = await self.conversation_repo.get_conversations_for_user(user_id)

        if not conversations:
            return []

        # ==================================================
        # 1️⃣ Gom toàn bộ participants của TẤT CẢ conversation
        # ==================================================
        user_ids_set = set()

        for conv in conversations:
            for p in conv["participants"]:
                user_ids_set.add(str(p["user_id"]))

        user_ids = list(user_ids_set)

        # ==================================================
        # 2️⃣ Batch profiles
        # ==================================================
        profiles = await self.user_profile_repo.get_public_by_ids(user_ids)
        profile_map = {
            str(profile["user_id"]): profile
            for profile in profiles
        }

        # ==================================================
        # 3️⃣ Batch avatars
        # ==================================================
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

        # ==================================================
        # 4️⃣ Gắn name + avatar vào từng conversation
        # ==================================================
        result = []

        for conv in conversations:
            participants_response = []

            for p in conv["participants"]:
                uid = (p["user_id"])
                profile = profile_map.get(uid)

                avatar_url = ""
                if profile and profile.get("avatar"):
                    media = media_map.get(str(profile["avatar"]))
                    avatar_url = media.get("url", "") if media else ""

                participants_response.append({
                    "user_id": uid,
                    "name": profile.get("display_name", "Người dùng") if profile else "Người dùng",
                    "avatar": avatar_url,
                    "joined_at": p["joined_at"]
                })

            result.append({
                "_id": conv["_id"],
                "participants": participants_response,
                "is_group": conv["is_group"],
                "created_at": conv["created_at"],
                "updated_at": conv.get("updated_at")
            })

        return result

    async def _get_existing_private_conversation(
            self,
            user_id: str,
            target_user_id: str
    ) -> ConversationResponse | None:

        existing_conversation_doc = await self.conversation_repo.find_by_participants(
            [user_id, target_user_id]
        )

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
