1️⃣ User tạo COMMENT GỐC:
Input từ UI:

post_id: ID bài viết
content: "Bài hay quá!"

Backend xử lý:

Tạo document mới với root_id = null
Tăng comments_count của post lên 1
Trả về comment mới cho UI


2️⃣ User REPLY comment gốc:
Input từ UI:

post_id: ID bài viết
reply_to_comment_id: ID comment được reply (ví dụ "c1")
content: "Mình cũng vậy"

Backend xử lý:

Lấy comment "c1" ra xem
Nếu "c1" là comment gốc (root_id = null) → set root_id = "c1"
Nếu "c1" là reply → lấy root_id của "c1"
Lưu reply_to_comment_id = "c1"
Lưu reply_to_user_id = user_id của comment "c1"
Tăng comments_count của post
Gửi notification cho user bị tag


3️⃣ User REPLY của REPLY:
Input từ UI:

Click reply ở comment "c2" (đã là reply rồi)
content: "Đồng ý"

Backend xử lý:

Lấy comment "c2" → thấy root_id = "c1"
Copy root_id = "c1" (giữ nguyên)
Set reply_to_comment_id = "c2" (khác root!)
Set reply_to_user_id = user_id của "c2"
Tăng comments_count của post
Gửi notification


4️⃣ Hiển thị COMMENTS:
Bước 1: Load comments gốc

Query post_id = "p1" và root_id = null
Sort theo created_at giảm dần
Phân trang 10 comment/trang

Bước 2: User click "View replies"

Query root_id = "c1"
Sort theo created_at tăng dần
Hiển thị flat list với tag user

Bước 3: Render UI

Comment gốc hiển thị bình thường
Replies thụt vào, có prefix "@Tên User"


5️⃣ Click NOTIFICATION (deep link):
URL: ?comment_id=c1&reply_comment_id=c3
Frontend xử lý:

Scroll đến comment c1
Expand replies của c1
Highlight comment c3

// Collection: comments
{
  "_id": ObjectId,
  "post_id": ObjectId,              // bài viết chứa comment
  "user_id": ObjectId,              // người comment
  "content": String,                // nội dung
  "has_replies": Boolean,           // Có phản hồi hay không
  
  // === THREADING FIELDS ===
  "root_id": ObjectId | null,       // null = comment gốc, có giá trị = reply
  "reply_to_comment_id": ObjectId | null,  // comment trực tiếp được reply
  "reply_to_user_id": ObjectId | null,     // user được tag (@mention)
  
  // === METADATA ===
  "created_at": ISODate,
  "updated_at": ISODate,
  
  // === INDEXES ===
  // Index 1: Lấy comment gốc của post
  // {post_id: 1, root_id: 1, created_at: -1}
  
  // Index 2: Lấy replies của 1 comment
  // {root_id: 1, created_at: 1}
}

---

## Kế hoạch Refactor

Thực hiện refactor theo đúng thứ tự và tuân thủ `GEMINI.md`.

### 1. Cập nhật Schema (`app/schemas/comment.py`)
- [x] Cập nhật `CommentCreate` để nhận `post_id`, `content`, và `reply_to_comment_id` (optional).
- [x] Cập nhật `CommentResponse` để trả về các trường mới: `root_id`, `reply_to_comment_id`, `reply_to_user_id`, cùng với thông tin người tạo comment.
- [x] Thêm `has_replies: bool` vào `CommentResponse`.

### 2. Cập nhật Repository (`app/repositories/comment_repository.py`)
- [x] Sửa đổi phương thức `create` để lưu document với cấu trúc mới.
- [x] Tạo phương thức `get_root_comments(post_id, skip, limit)` để lấy các bình luận gốc, sắp xếp theo `created_at` giảm dần.
- [x] Tạo phương thức `get_replies(root_id, skip, limit)` để lấy các trả lời trong một luồng, sắp xếp theo `created_at` tăng dần.

### 3. Cập nhật Service (`app/services/comment_service.py`)
- [x] Refactor logic của `create_comment` để xử lý 2 trường hợp:
    - **Tạo comment gốc:** Khi `reply_to_comment_id` không có. `root_id` sẽ là `null`.
    - **Tạo reply:** Khi `reply_to_comment_id` có.
        - Lấy `parent_comment` từ `reply_to_comment_id`.
        - Xác định `root_id` (lấy từ `parent_comment.root_id` hoặc `parent_comment.id`).
        - Gán `reply_to_user_id` từ `parent_comment.user_id`.
- [x] Đảm bảo logic tăng `comments_count` của bài viết vẫn hoạt động.
- [x] Logic phải là non-blocking (`async/await`) theo quy tắc của `GEMINI.md`.

### 4. Cập nhật Dependencies (`app/api/deps.py`)
- [x] Kiểm tra và đảm bảo `CommentService` và các dependencies liên quan được cung cấp chính xác. (Thường không cần thay đổi lớn ở bước này).

### 5. Cập nhật Endpoint (`app/api/v1/endpoints/comments.py`)
- [x] Cập nhật endpoint `POST /` để sử dụng `CommentCreate` schema mới.
- [x] Tạo endpoint `GET /posts/{post_id}/comments` để lấy danh sách bình luận gốc (có phân trang).
- [x] Tạo endpoint `GET /comments/{comment_id}/replies` để lấy danh sách các trả lời (có phân trang).

### 6. Cập nhật Database Indexes
- [x] Cập nhật file `scripts/setup_mongo_indexes.py` để thêm các index mới đã được định nghĩa trong `refactor_comment.md`, giúp tối ưu hóa các query.
