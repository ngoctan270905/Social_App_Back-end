# Kế hoạch Triển khai Chat Realtime (WebSocket)

Tài liệu này mô tả chi tiết các bước cần thiết để nâng cấp hệ thống chat hiện tại từ cơ chế Request/Response (API) sang Realtime (WebSocket).

## Kiến trúc Tổng quan

1.  **Client (Frontend)**: Duy trì một kết nối WebSocket duy nhất tới Server.
2.  **Server (Backend)**:
    *   **ConnectionManager**: Quản lý danh sách các kết nối, map `user_id` với `websocket_connection`.
    *   **MessageService**: Khi lưu tin nhắn vào DB xong, sẽ gọi `ConnectionManager` để bắn tín hiệu tới người nhận (và người gửi để đồng bộ đa thiết bị).

---

## Phần 1: Backend (FastAPI)

### Bước 1: Nâng cấp `ConnectionManager`
**File:** `back-end/app/core/websocket.py`

Thay đổi từ việc quản lý list đơn giản sang quản lý theo User ID.

```python
import logging
from typing import Dict, List
from fastapi import WebSocket

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # Key: user_id, Value: List các kết nối (1 user có thể dùng nhiều tab/thiết bị)
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        logger.info(f"User {user_id} connected. Total connections: {sum(len(v) for v in self.active_connections.values())}")

    def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info(f"User {user_id} disconnected.")

    async def send_personal_message(self, message: dict, user_id: str):
        """Gửi tin nhắn tới một user cụ thể (trên mọi thiết bị của họ)"""
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending to {user_id}: {e}")
                    # Có thể cân nhắc disconnect nếu lỗi
    
    async def broadcast(self, message: dict):
        """Gửi cho tất cả (nếu cần)"""
        for user_id, connections in self.active_connections.items():
            for connection in connections:
                await connection.send_json(message)

manager = ConnectionManager()
```

### Bước 2: Xác thực & Endpoint WebSocket
**File:** `back-end/app/api/v1/endpoints/websockets.py`

Sử dụng `verify_scoped_token` để xác thực JWT token từ query param. Cần inject `redis_client` để kiểm tra blacklist.

```python
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
        # 1. Validate Token (Real Logic)
        try:
            # verify_scoped_token sẽ raise HTTPException nếu token không hợp lệ hoặc hết hạn
            # "access_token" là scope bắt buộc cho token đăng nhập
            user_id = await verify_scoped_token(token, "access_token", redis_client)
        except HTTPException as e:
            logger.warning(f"WebSocket authentication failed: {e.detail}")
            # Đóng kết nối với code 1008 (Policy Violation) nếu auth fail
            await websocket.close(code=1008)
            return
        except Exception as e:
             logger.error(f"Token validation error: {e}")
             await websocket.close(code=1008)
             return
        
        if not user_id:
            await websocket.close(code=1008)
            return

        # 2. Connect
        await manager.connect(websocket, user_id)
        
        # 3. Listen loop
        try:
            while True:
                # Giữ kết nối, có thể xử lý ping/pong hoặc sự kiện từ client gửi lên (typing...)
                data = await websocket.receive_text()
                # await manager.handle_message(websocket, data)
        except WebSocketDisconnect:
            manager.disconnect(websocket, user_id)
            
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        # Thử đóng kết nối nếu chưa đóng
        try:
            await websocket.close()
        except RuntimeError:
            pass # Kết nối đã đóng
```

### Bước 3: Tích hợp vào `MessageService`
**File:** `back-end/app/services/message_service.py`

Sau khi lưu tin nhắn, bắn event socket.

```python
from app.core.websocket import manager # Import manager

# ... trong class MessageService ...

    async def send_message(self, sender_id: str, conversation_id: str, data: MessageCreate) -> MessageResponse:
        # 1. Lưu vào DB (Code cũ)
        msg = await self.message_repo.create(
            conversation_id=conversation_id,
            sender_id=sender_id,
            content=data.content
        )
        
        response_msg = MessageResponse(**msg)
        
        # 2. Lấy thông tin cuộc hội thoại để biết người nhận (Target User)
        # Sử dụng ConversationRepository để lấy raw document (vì cần list participants)
        conversation = await self.conversation_repo.get_by_id(conversation_id)
        
        # 3. Gửi Realtime
        payload = {
            "type": "new_message",
            "conversation_id": conversation_id,
            "data": response_msg.dict() # Convert model to dict
        }

        # Gửi cho các thành viên trong nhóm
        # Structure của participants trong DB: [{"user_id": ObjectId(...), ...}, ...]
        if conversation and "participants" in conversation:
            for p in conversation["participants"]:
                # user_id trong participants là ObjectId, cần convert sang string
                p_id = str(p["user_id"])
                
                # Gửi cho tất cả (bao gồm cả sender để update UI real-time trên các tab khác của họ)
                await manager.send_personal_message(payload, p_id)

        return response_msg
```

---

## Phần 2: Frontend (React)

### Bước 4: Tạo WebSocket Service
**File:** `front-end/src/services/socketService.ts`

Quản lý kết nối singleton để dùng chung cho toàn app.

```typescript
type MessageHandler = (data: any) => void;

class SocketService {
    private socket: WebSocket | null = null;
    private handlers: MessageHandler[] = [];
    
    connect(token: string) {
        if (this.socket) return; // Đã kết nối

        // URL backend
        const wsUrl = `ws://localhost:8000/api/v1/ws/chat?token=${token}`;
        this.socket = new WebSocket(wsUrl);

        this.socket.onopen = () => {
            console.log("WebSocket Connected");
        };

        this.socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handlers.forEach(handler => handler(data));
        };

        this.socket.onclose = () => {
            console.log("WebSocket Disconnected. Reconnecting...");
            this.socket = null;
            // Logic reconnect có thể thêm ở đây (setTimeout)
            setTimeout(() => this.connect(token), 3000);
        };
        
        this.socket.onerror = (err) => {
            console.error("WebSocket Error:", err);
        };
    }

    disconnect() {
        if (this.socket) {
            this.socket.close();
            this.socket = null;
        }
    }

    // Đăng ký nhận tin
    subscribe(handler: MessageHandler) {
        this.handlers.push(handler);
        // Trả về hàm cleanup để component unmount thì unsubscribe
        return () => {
            this.handlers = this.handlers.filter(h => h !== handler);
        };
    }
}

export const socketService = new SocketService();
```

### Bước 5: Kết nối khi Login
**File:** `front-end/src/contexts/AuthContext.tsx` hoặc `App.tsx`

Khi user login thành công và có Token, gọi `socketService.connect(token)`.

### Bước 6: Cập nhật ChatBox UI
**File:** `front-end/src/components/chat/ChatBox.tsx`

```typescript
import { socketService } from '../../services/socketService';

// ...

  useEffect(() => {
    // 1. Subscribe nhận tin nhắn realtime
    const unsubscribe = socketService.subscribe((event) => {
        if (event.type === 'new_message') {
            const incomingMsg = event.data;
            
            // Kiểm tra xem tin nhắn có thuộc hội thoại đang mở không
            if (incomingMsg.conversation_id === user?.conversationId) {
                setMessages(prev => [...prev, incomingMsg]);
                
                // Scroll xuống dưới cùng nếu đang ở gần đáy
                if (messagesContainerRef.current) {
                    // Logic check scroll...
                    messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight;
                }
            } else {
                // TODO: Hiển thị thông báo đỏ (Notification Badge) ở list chat hoặc header
                console.log("Có tin nhắn mới từ cuộc hội thoại khác:", incomingMsg);
            }
        }
    });

    return () => {
        unsubscribe(); // Cleanup khi đóng chatbox
    };
  }, [user?.conversationId]); // Re-run nếu đổi conversation
```

---

## Các bước tiếp theo

1.  **Backup Code**: Tạo commit git trước khi sửa core backend.
2.  **Triển khai Backend**: Thực hiện bước 1, 2, 3 ở trên. Test bằng Postman (WebSocket Request).
3.  **Triển khai Frontend**: Thực hiện bước 4, 5, 6.
4.  **Test**: Mở 2 trình duyệt, login 2 tài khoản khác nhau và chat thử.

