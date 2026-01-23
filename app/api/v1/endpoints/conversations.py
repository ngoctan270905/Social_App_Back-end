from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.api import deps
from app.api.deps import get_message_service, get_conversation_service
from app.core.dependencies import get_current_user
from app.schemas.conversation import ConversationResponse, ConversationFindOrCreate, ConversationListItem
from app.schemas.message import MessageCreate, MessageResponse
from app.schemas.response import ResponseModel
from app.services.message_service import MessageService
from app.repositories.message_repository import MessageRepository
from app.services.conversation_service import ConversationService
from app.repositories.conversation_repository import ConversationRepository

router = APIRouter()


@router.post("/",
    response_model=ResponseModel[ConversationResponse],
    status_code=status.HTTP_200_OK,
    summary="Tạo cuộc trò chuyện mới"
)
async def find_or_create_conversation(
        *,
        data: ConversationFindOrCreate,
        current_user: dict = Depends(get_current_user),
        service: ConversationService = Depends(get_conversation_service)
):

    target_user_id = data.target_user_id
    print(f"target_user_id: {target_user_id}")

    conversation = await service.find_or_create_private_conversation(
        user_id=str(current_user["_id"]),
        target_user_id=target_user_id
    )
    return ResponseModel(data=conversation, message="Tạo cuộc trò chuyện thành công")


# Gửi tin nhắn =========================================================================================================
@router.post("/a", response_model=ResponseModel[MessageResponse], status_code=status.HTTP_201_CREATED)
async def send_message(
    *,
    message_in: MessageCreate,
    current_user: dict = Depends(get_current_user),
    message_service: MessageService = Depends(get_message_service)
):
    message = await message_service.send_message(sender_id=current_user["_id"], data=message_in)
    return ResponseModel(data=message, message="Gửi tin nhắn thành công")



# Danh sách cuộc trò chuyện ============================================================================================
@router.get("/", response_model=ResponseModel[List[ConversationListItem]], status_code=status.HTTP_200_OK)
async def get_conversations(
    *,
    current_user: dict = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    conversations = await conversation_service.get_conversations_for_user(user_id=current_user["_id"])
    return ResponseModel(data=conversations, message="Lấy danh sách cuộc trò chuyện thành công")



# Chi tiết cuộc trò chuyện =============================================================================================
@router.get("/{conversation_id}/messages", response_model=ResponseModel[List[MessageResponse]], status_code=status.HTTP_200_OK)
async def get_messages(
    *,
    conversation_id: str,
    current_user: dict = Depends(get_current_user),
    message_service: MessageService = Depends(get_message_service),
    skip: int = 0,
    limit: int = 50
):

    messages = await message_service.detail_message(conversation_id, skip=skip, limit=limit)
    return ResponseModel(data=messages, message="Lấy tin nhắn thành công")