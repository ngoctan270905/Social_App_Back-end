from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from app.services.notification_service import NotificationService
from app.api.deps import get_notification_service

router = APIRouter()

@router.get("/stream")
async def stream_notifications(
    request: Request,
    service: NotificationService = Depends(get_notification_service)
):
    """
    SSE Endpoint: Kết nối liên tục để nhận thông báo.
    """
    return StreamingResponse(
        service.notification_generator(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
            "X-Accel-Buffering": "no",
        }
    )