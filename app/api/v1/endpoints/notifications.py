from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_notification_service
from app.core.dependencies import get_current_user
from app.schemas.notification import Notification
from app.schemas.response import ResponseModel
from app.services.notification_service import NotificationService

router = APIRouter()

@router.get(
    "/",
    response_model=ResponseModel[List[Notification]],
    summary="Lấy danh sách thông báo của người dùng"
)
async def get_my_notifications(
    current_user: dict = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100),
    cursor: Optional[str] = Query(None),
    service: NotificationService = Depends(get_notification_service)
):
    notifications = await service.get_notifications_for_user(user_id=str(current_user["_id"]), limit=limit, cursor=cursor)
    return ResponseModel(data=notifications)

@router.post(
    "/{notification_id}/read",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Đánh dấu một thông báo là đã đọc"
)
async def mark_notification_as_read(
    notification_id: str,
    current_user: dict = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service)
):
    await service.mark_notification_as_read(notification_id=notification_id, user_id=str(current_user["_id"]))
    return None
