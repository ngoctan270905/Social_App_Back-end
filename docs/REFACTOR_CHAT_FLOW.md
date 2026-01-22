# Refactoring the Chat Flow

## 1. Objective

To refactor the chat creation and message sending flow to align with the logic described in `flow.txt`. This will create a more robust, efficient, and semantically clear API.

The new flow is:
1.  User clicks "Message" on another user's profile.
2.  Frontend calls a single backend endpoint to either find the existing conversation or create a new one.
3.  Backend always returns a valid `conversation_id`.
4.  Frontend opens the chat box using this `conversation_id` to fetch messages.

---

## 2. Backend Implementation

### 2.0. New Schemas

We need to define new Pydantic schemas for request bodies.

**File:** `Social_App_Back-end/app/schemas/conversation.py`
```python
# Thêm schema mới này vào app/schemas/conversation.py
class ConversationFindOrCreate(BaseModel):
    target_user_id: str
```

**File:** `Social_App_Back-end/app/schemas/message.py` (Assuming message schemas are here, or create a new `chat_request.py`)
```python
# Thêm schema mới này vào app/schemas/message.py (hoặc một file schema cho request riêng)
from pydantic import BaseModel

class MessageCreateContent(BaseModel):
    content: str
```

### 2.1. New Endpoint: Find or Create Conversation

We will create a new endpoint dedicated to finding or creating a conversation.

- **File:** `Social_App_Back-end/app/api/v1/endpoints/chat.py` (or a new `conversations.py`)
- **Endpoint:** `POST /api/v1/conversations`
- **Request Body:** `{ "target_user_id": "string" }`
- **Response Body:** `Conversation` object.

**Router Code (`chat.py`):**
```python
# Trong file router chat của bạn

from app.services.conversation_service import ConversationService
from app.schemas.conversation import ConversationFindOrCreate # Import schema mới
# ... các import khác (User, Depends, deps, HTTPException, status)

@router.post(
    "/conversations",
    response_model=Conversation,
    status_code=status.HTTP_200_OK,
    summary="Tìm hoặc tạo một cuộc trò chuyện 1-1"
)
async def find_or_create_conversation(
    *,
    body: ConversationFindOrCreate, # Sử dụng schema mới ở đây
    current_user: User = Depends(deps.get_current_active_user),
    service: ConversationService = Depends()
):
    """
    Tìm một cuộc trò chuyện giữa người dùng hiện tại và người dùng mục tiêu.
    - Nếu cuộc trò chuyện đã tồn tại, nó sẽ trả về cuộc trò chuyện hiện có.
    - Nếu không có cuộc trò chuyện nào, nó sẽ tạo một cuộc trò chuyện mới và trả về nó.
    """
    # Truy cập target_user_id trực tiếp từ Pydantic model
    target_user_id = body.target_user_id
    
    # Không cần xác thực sự tồn tại thủ công, Pydantic xử lý các trường bắt buộc
    
    conversation = await service.find_or_create_private_conversation(
        user_id=str(current_user.id),
        target_user_id=target_user_id
    )
    return conversation
```

**Service Code (`conversation_service.py`):**
```python
# Trong lớp ConversationService

from app.repositories.conversation_repository import ConversationRepository
from app.repositories.user_repository import UserRepository
from app.repositories.user_profile_repository import UserProfileRepository
from app.schemas.conversation import ConversationResponse, ParticipantEmbedded # Import các schema cần thiết
from app.core.exceptions import base as exceptions # Dùng cho các exception tùy chỉnh
from bson import ObjectId
from datetime import datetime

class ConversationService:
    def __init__(
        self, 
        repo: ConversationRepository = Depends(),
        user_repo: UserRepository = Depends(),
        profile_repo: UserProfileRepository = Depends()
    ):
        self.repo = repo
        self.user_repo = user_repo
        self.profile_repo = profile_repo

    async def find_or_create_private_conversation(self, user_id: str, target_user_id: str) -> ConversationResponse:
        """
        Tìm hoặc tạo một cuộc trò chuyện 1-1 giữa hai người dùng,
        đồng thời điền đầy đủ thông tin chi tiết của người tham gia (tên, avatar).
        """
        if user_id == target_user_id:
            raise exceptions.BadRequestException("Không thể tạo cuộc trò chuyện với chính mình.")

        # 1. Kiểm tra xem cuộc trò chuyện giữa hai người này đã tồn tại chưa
        # Phương thức này cần được triển khai/cập nhật trong ConversationRepository
        existing_conversation_doc = await self.repo.find_by_participants([user_id, target_user_id])
        
        if existing_conversation_doc:
            return ConversationResponse(**existing_conversation_doc)

        # 2. Nếu chưa, lấy thông tin chi tiết của cả hai người dùng để tạo đối tượng participant
        user_doc = await self.user_repo.get_by_id(user_id)
        target_user_doc = await self.user_repo.get_by_id(target_user_id)
        
        user_profile_doc = await self.profile_repo.get_by_user_id(user_id)
        target_user_profile_doc = await self.profile_repo.get_by_user_id(target_user_id)

        if not all([user_doc, target_user_doc, user_profile_doc, target_user_profile_doc]):
            raise exceptions.NotFoundException("Không tìm thấy một hoặc nhiều người dùng.")

        # 3. Tạo danh sách các đối tượng ParticipantEmbedded
        participants_to_embed = [
            ParticipantEmbedded(
                user_id=ObjectId(user_id),
                name=user_doc.get("username", "Người dùng không xác định"),
                avatar=user_profile_doc.get("avatar", "") # Giả sử avatar là một URL dạng chuỗi
            ),
            ParticipantEmbedded(
                user_id=ObjectId(target_user_id),
                name=target_user_doc.get("username", "Người dùng không xác định"),
                avatar=target_user_profile_doc.get("avatar", "") # Giả sử avatar là một URL dạng chuỗi
            )
        ]

        # 4. Tạo cuộc trò chuyện mới với dữ liệu participant đầy đủ
        new_conversation_data = {
            "participants": [p.dict() for p in participants_to_embed],
            "participant_ids": [ObjectId(user_id), ObjectId(target_user_id)], # Giữ lại trường này để truy vấn
            "is_group": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        created_conversation_doc = await self.repo.create(new_conversation_data)
        return ConversationResponse(**created_conversation_doc)

```
**Repository Code (`conversation_repository.py`):**
```python
# Phương thức này cần được thêm vào lớp ConversationRepository

from typing import List, Optional, Dict, Any
from bson import ObjectId

class ConversationRepository:
    # ... các phương thức hiện có

    async def find_by_participants(self, participant_ids: List[str]) -> Optional[Dict[str, Any]]:
        """
        Tìm một cuộc trò chuyện 1-1 dựa trên ID của người tham gia.
        Giả định participant_ids là các chuỗi có thể chuyển đổi thành ObjectId.
        """
        object_ids = [ObjectId(p_id) for p_id in participant_ids]
        
        # Truy vấn này tìm một cuộc trò chuyện có chính xác hai người tham gia này
        # và không có người nào khác (cho cuộc trò chuyện riêng tư)
        # và cũng xem xét trường hợp thứ tự của người tham gia có thể bị tráo đổi trong DB
        
        # Điều này có thể cần tinh chỉnh dựa trên cách 'participants' được lưu trữ và lập chỉ mục.
        # Để đơn giản, giả sử có một trường mảng 'participant_ids'.
        query = {
            "participant_ids": { "$all": object_ids, "$size": len(object_ids) },
            "is_group": False # Chỉ xem xét các cuộc trò chuyện riêng tư
        }
        return await self.collection.find_one(query)

    async def create(self, conversation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Tạo một document cuộc trò chuyện mới.
        """
        result = await self.collection.insert_one(conversation_data)
        conversation_data["_id"] = result.inserted_id
        return conversation_data
```

### 2.2. Modified Endpoint: Send Message

We will refactor the "send message" endpoint to be more RESTful and simpler. The old `POST /chats` will be removed or replaced.

- **File:** `Social_App_Back-end/app/api/v1/endpoints/chat.py`
- **Endpoint:** `POST /api/v1/conversations/{conversation_id}/messages`
- **Request Body:** `{ "content": "string" }`
- **Response Body:** `Message` object.

**Router Code (`chat.py`):**
```python
# Trong file router chat của bạn

from app.services.message_service import MessageService
from app.schemas.message import MessageCreateContent # Import schema mới cho nội dung tin nhắn
# ... các import khác (User, Depends, deps, HTTPException, status, Message)

@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=Message, # Giả sử Message là response model cho tin nhắn
    status_code=status.HTTP_201_CREATED,
    summary="Gửi một tin nhắn vào cuộc trò chuyện"
)
async def send_message_to_conversation(
    *,
    conversation_id: str,
    body: MessageCreateContent, # Sử dụng schema mới ở đây
    current_user: User = Depends(deps.get_current_active_user),
    message_service: MessageService = Depends()
):
    """
    Tạo một tin nhắn mới trong một cuộc trò chuyện cụ thể.
    """
    content = body.content # Truy cập content trực tiếp từ Pydantic model

    # Không cần xác thực sự tồn tại thủ công, Pydantic xử lý các trường bắt buộc
    
    # Service sẽ xử lý việc kiểm tra người dùng có phải là người tham gia không và tạo tin nhắn
    new_message = await message_service.create_message(
        conversation_id=conversation_id,
        sender_id=str(current_user.id),
        content=content
    )
    return new_message
```
**Service Code (`message_service.py`):**
```python
# Phương thức này cần được triển khai/cập nhật trong lớp MessageService

from app.repositories.message_repository import MessageRepository
from app.repositories.conversation_repository import ConversationRepository
from app.core.timezone import now_vn # Import để lấy thời gian local

class MessageService:
    def __init__(self, message_repo: MessageRepository = Depends(), conversation_repo: ConversationRepository = Depends()):
        self.message_repo = message_repo
        self.conversation_repo = conversation_repo

    async def create_message(self, conversation_id: str, sender_id: str, content: str) -> MessageResponse:
        """
        Tạo một tin nhắn mới và thêm nó vào cuộc trò chuyện được chỉ định.
        Bao gồm xác thực để đảm bảo người gửi là một người tham gia của cuộc trò chuyện.
        """
        # 1. Xác thực nếu cuộc trò chuyện tồn tại và người gửi là một người tham gia
        conversation_doc = await self.conversation_repo.get_by_id(conversation_id)
        if not conversation_doc:
            raise HTTPException(status_code=404, detail="Không tìm thấy cuộc trò chuyện.")
        
        # Giả sử participant_ids là một danh sách ObjectId trong document của cuộc trò chuyện
        participant_ids_str = [str(p_id) for p_id in conversation_doc.get("participant_ids", [])]
        if sender_id not in participant_ids_str:
            raise HTTPException(status_code=403, detail="Không phải là người tham gia của cuộc trò chuyện này.")

        # 2. Tạo document tin nhắn
        new_message_data = {
            "conversation_id": ObjectId(conversation_id),
            "sender_id": ObjectId(sender_id),
            "content": content,
            "created_at": now_vn(), # Sử dụng múi giờ Việt Nam
            "updated_at": now_vn()
        }
        
        created_message_doc = await self.message_repo.create(new_message_data)
        
        # 3. Cập nhật dấu thời gian updated_at của cuộc trò chuyện
        await self.conversation_repo.update_updated_at(conversation_id, now_vn())

        return MessageResponse(**created_message_doc)
```

---

## 3. Frontend Implementation

### 3.1. Chat Service (`chatService.ts`)

The service will be updated with a new method and the `sendMessage` method will be modified.

```typescript
// src/services/chatService.ts
import api from '../lib/axios';
// Assuming ApiResponse is defined elsewhere or directly used as response.data
import type { Conversation, MessageResponse } from '../types/chat';

// The API response is wrapped in a 'data' and 'message' field.
interface ApiResponse<T> {
  data: T;
  message: string;
}

class ChatService {
  
  // New method
  async findOrCreateConversation(targetUserId: string): Promise<Conversation> {
    const response = await api.post<ApiResponse<Conversation>>('/conversations', { target_user_id: targetUserId });
    return response.data.data;
  }

  // This method needs to be updated to match the new backend endpoint for fetching messages
  // Assuming the backend will have GET /api/v1/conversations/{conversation_id}/messages
  async getMessages(conversationId: string): Promise<MessageResponse[]> {
    const response = await api.get<ApiResponse<MessageResponse[]>>(`/conversations/${conversationId}/messages`);
    return response.data.data;
  }

  // Modified method
  async sendMessage(
    content: string,
    conversationId: string, // No longer optional
  ): Promise<MessageResponse> {
    const messageData = { content };
    const response = await api.post<ApiResponse<MessageResponse>>(
        `/conversations/${conversationId}/messages`, 
        messageData
    );
    return response.data.data;
  }
  
  // ... other methods (getConversations)
  // The existing getConversations method:
  async getConversations(): Promise<Conversation[]> {
    const response = await api.get<ApiResponse<Conversation[]>>('/chats/'); // This URL might also need to be updated to /conversations
    return response.data.data;
  }
}

export default new ChatService();
```

### 3.2. User Profile Page (Example Logic)

The component that has the "Message" button (e.g., a User Profile page) will now handle the logic to get the conversation ID.

```typescript
// Example in a component like UserProfile.tsx

import React from 'react';
import chatService from '../../services/chatService';
import { useChat } from '../../contexts/ChatContext'; // Assuming a context to manage chat state
import type { Conversation, ParticipantDetail } from '../../types/chat'; // Import Conversation type

interface UserProfileProps {
  profileUser: {
    id: string;
    name: string;
    avatar: string;
    // ... other user details
  };
}

const UserProfile: React.FC<UserProfileProps> = ({ profileUser }) => {
  const { openChat } = useChat(); // openChat function from context

  const handleMessageClick = async () => {
    try {
      // 1. Call the new service method to find or create conversation
      const conversation: Conversation = await chatService.findOrCreateConversation(profileUser.id);
      
      // 2. Open the chat box, passing the necessary details
      if (conversation) {
        // Construct the participant detail based on the other user in the conversation
        const otherParticipant = conversation.participants.find(
          p => p.user_id !== profileUser.id // Assuming current user's ID is managed by AuthContext
        );

        if (!otherParticipant) {
          console.error("Other participant not found in conversation.");
          return;
        }

        // Assuming profileUser already has id, name, avatar
        const chatParticipantDetail: ParticipantDetail = {
            id: otherParticipant.user_id,
            name: profileUser.name, // Assuming profileUser is the target user
            avatar: profileUser.avatar, // Assuming profileUser is the target user
        };

        openChat({
          conversationId: conversation.id,
          participant: chatParticipantDetail,
        });
      }
    } catch (error) {
      console.error("Failed to start conversation", error);
      // Handle error (e.g., show a notification)
    }
  };

  return (
    <div>
      {/* ... profile info ... */}
      <button onClick={handleMessageClick}>Nhắn tin</button>
    </div>
  );
};

export default UserProfile;
```

### 3.3. ChatBox Component (`ChatBox.tsx`)

The `ChatBox` component will become much simpler. It will receive the `conversationId` as a prop and use it directly.

```typescript
// src/components/chat/ChatBox.tsx

// ... imports
// import type { MessageResponse } from '../../types/chat'; // Already imported if using ChatBoxProps
// import { useAuth } from '../../contexts/AuthContext'; // Needed if getting current user info

interface ParticipantDetail {
  id: string | null;
  name: string;
  avatar: string;
}

interface ChatBoxDetail {
  conversationId: string;
  participant: ParticipantDetail;
}

interface ChatBoxProps {
  isOpen: boolean;
  onClose: () => void;
  user?: ChatBoxDetail; // This user prop now contains the pre-resolved conversationId and participant
}


const ChatBox: React.FC<ChatBoxProps> = ({ isOpen, onClose, user }) => {
  const [messages, setMessages] = useState<MessageResponse[]>([]);
  const [messageError, setMessageError] = useState<string | null>(null);
  const { user: currentUser } = useAuth(); // Assuming this is how you get the current user
  // ... other refs/states

  // The main useEffect is now much simpler
  useEffect(() => {
    const loadMessages = async () => {
        // Now, we always expect user.conversationId to be present if isOpen is true
        if (isOpen && user?.conversationId) {
            try {
                // It receives the conversationId directly, no need to find it
                const fetchedMessages = await chatService.getMessages(user.conversationId);
                const sortedMessages = fetchedMessages.sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());
                setMessages(sortedMessages);
                setMessageError(null); // Clear any previous errors
            } catch (err: any) {
                 console.error("Error loading messages:", err);
                 setMessageError("Failed to load messages."); // Set a user-friendly error
                 setMessages([]);
            }
        } else if (!isOpen) {
            // Reset messages when chat box is closed
            setMessages([]);
            setMessageError(null);
        }
    };

    loadMessages();
  }, [isOpen, user?.conversationId]); // Dependency is now just the conversationId

  // The handleSendMessage is also simpler
  const handleSendMessage = async () => {
    // We now guarantee user.conversationId exists before calling sendMessage
    if (inputValue.trim() === '' || !user?.conversationId) return; 

    try {
      const newMessage = await chatService.sendMessage(
        inputValue,
        user.conversationId
      );
      setMessages((prevMessages) => [...prevMessages, newMessage]);
      setInputValue('');
    } catch (error) {
      setMessageError('Failed to send message.');
      console.error('Error sending message:', error);
    }
  };

  // ... rest of the component (return statement)
  return (
    <>
      <style>{`
        /* ... existing styles ... */
      `}</style>

      {/* Chat Container */}
      <div 
        className={`fixed bottom-0 right-20 z-40 w-[328px] bg-[#242526] rounded-t-lg shadow-2xl overflow-hidden flex flex-col font-sans border border-[#3e4042] transition-all duration-300 ease-in-out ${user?.conversationId ? 'h-[455px]' : 'h-[48px]'}`} 
        // Adjust height based on whether a conversation is active
      >
        {/* ... Header ... */}
        {/* Messages Area */}
        <div ref={messagesContainerRef} className="gradient-header flex-1 overflow-y-auto" style={{ height: '400px' }}>
            <div className="pt-4 px-1 pb-0 space-y-4">
                {/* ... Profile Info ... */}
                {messageError && <p className="text-center text-red-500">Error: {messageError}</p>}
                {!messageError && messages.length === 0 && (
                    <p className="text-center text-[#b0b3b8]">{user?.conversationId ? "Chưa có tin nhắn nào." : "Click 'Nhắn tin' để bắt đầu cuộc trò chuyện."}</p>
                )}
                {/* ... Messages map ... */}
            </div>
        </div>
        {/* Input Area */}
        {user?.conversationId && ( // Only show input area if a conversation is active
            <div className="bg-[#242526] px-2 py-2">
                {/* ... Input and buttons ... */}
            </div>
        )}
      </div>
    </>
  );
};

export default ChatBox;
```