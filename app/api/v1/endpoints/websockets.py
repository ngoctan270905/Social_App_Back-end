from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends, HTTPException
from app.core.websocket import manager
from app.core.security import verify_scoped_token
from app.core.redis_client import get_redis_client
import redis.asyncio as redis
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.websocket("/ws/chat")
async def websocket_endpoint(
        websocket: WebSocket,
        token: str = Query(...),
        redis_client: redis.Redis = Depends(get_redis_client)
):
    try:
        # 1. Validate Token
        try:
            user_id = await verify_scoped_token(token, "access_token", redis_client)
        except HTTPException as e:
            logger.warning(f"Xác thực web scoket thất bại: {e.detail}")
            await websocket.accept()
            await websocket.close(code=1008)
            return
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            await websocket.accept()
            await websocket.close(code=1008)
            return

        if not user_id:
            await websocket.accept()
            await websocket.close(code=1008)
            return

        # 2. Connect
        await manager.connect(websocket, user_id)

        # 3. Listen loop
        try:
            while True:
                data = await websocket.receive_text()
        except WebSocketDisconnect:
            manager.disconnect(websocket, user_id)

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.close()
        except RuntimeError:
            pass