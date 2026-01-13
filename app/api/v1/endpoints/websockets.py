import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.websocket import manager

logger = logging.getLogger(__name__)
router = APIRouter()

@router.websocket("/ws/news")
async def websocket_endpoint(websocket: WebSocket):
    logger.info("Client đang kết nối WebSocket tới /ws/news")
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.handle_message(websocket, data)
    except WebSocketDisconnect:
        manager.disconnect(websocket)