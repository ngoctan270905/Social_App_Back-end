from typing import List, Optional
from fastapi import APIRouter, Depends, Query

from app.api.deps import get_notification_service
from app.core.dependencies import get_current_user
from app.schemas.notification import Notification
from app.schemas.response import ResponseModel
from app.services.notification_service import NotificationService

router = APIRouter()

@router.get(
    "/",
    response_model=ResponseModel[List[Notification]],
    summary="Lấy danh sách thông báo của người dùng hiện tại"
)
async def get_my_notifications(
    current_user: dict = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100),
    cursor: Optional[str] = Query(None),
    service: NotificationService = Depends(get_notification_service)
):
    """
    Lấy danh sách thông báo cho người dùng đã đăng nhập, sắp xếp theo thứ tự mới nhất.
    """
    user_id = str(current_user["_id"])
    notifications = await service.get_notifications_for_user(user_id=user_id, limit=limit, cursor=cursor)
    return ResponseModel(
        data=notifications,
        message="Lấy danh sách thông báo thành công."
    )
