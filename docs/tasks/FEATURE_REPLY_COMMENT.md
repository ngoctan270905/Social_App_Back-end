# Kế hoạch Triển khai Tính năng Trả lời Bình luận (Reply Comment)

Tài liệu này mở rộng từ `FEATURE_ADD_COMMENT_API.md`, tập trung vào việc xử lý logic phản hồi bình luận (Nested Comments).

## 1. Phân tích & Thiết kế Database

### 1.1. Cập nhật Collection `comments`
Chúng ta sẽ sử dụng mô hình **Parent Reference** kết hợp với **Denormalization** (đếm số reply) để tối ưu hiệu năng đọc (Read-heavy).

| Field | Type | Description | Index |
| :--- | :--- | :--- | :--- |
| `parent_id` | ObjectId | ID của comment cha. Nếu là null -> Root comment. | **Indexed** |
| `reply_count` | Int | Số lượng phản hồi trực tiếp của comment này. | |
| `post_id`| ObjectId | Reference to `posts` (Bắt buộc cho cả Reply để query/delete nhanh). | **Indexed** |

**Index Strategy:**
- Compound Index: `{ parent_id: 1, created_at: 1 }` -> Để query danh sách reply của 1 comment theo thứ tự thời gian.
- Compound Index: `{ post_id: 1, created_at: -1 }` -> (Đã có) Để lấy root comments.

### 1.2. Chiến lược Update (Write Path)
Khi User B trả lời comment của User A:
1. **Insert**: Tạo document mới trong `comments` với `parent_id = UserA_Comment_ID`.
2. **Update Parent**: Tăng `reply_count` của comment cha (`$inc`).
3. **Update Post**: Tăng tổng `comments_count` của bài viết gốc (`$inc`).

> **Lưu ý GEMINI.md**: Các thao tác write này nên được thực hiện song song (Parallel) hoặc dùng Transaction (nếu cần tính nhất quán tuyệt đối), nhưng không được block main thread. Với MVP, có thể dùng `await` tuần tự nhưng phải handle lỗi rollback nếu bước sau fail.

---

## 2. API Design

### 2.1. Create Reply
Sử dụng chung Endpoint tạo comment, nhưng thêm `parent_id`.

- **Endpoint**: `POST /api/v1/comments/`
- **Body**:
  ```json
  {
    "post_id": "...",
    "content": "Nội dung trả lời",
    "parent_id": "..." // Optional: Nếu có field này thì là reply
  }
  ```

### 2.2. Get Replies (Lazy Loading)
Không trả về toàn bộ cây comment (Tree) một lúc. Client sẽ load comment gốc, khi user bấm "Xem trả lời", sẽ gọi API này.

- **Endpoint**: `GET /api/v1/comments/{comment_id}/replies`
- **Query Params**: `page`, `limit` (Default 10)
- **Response**: Danh sách comment con.

---

## 3. Cấu trúc Source Code

### A. Schemas (`app/schemas/comment.py`)
- Uncomment `parent_id` trong `CommentCreate`.
- Thêm `parent_id` và `reply_count` vào `CommentResponse`.

### B. Repository (`app/repositories/comment_repository.py`)
- Update hàm `create`: Xử lý thêm `parent_id`.
- Thêm hàm `get_by_parent_id`: Lấy danh sách reply, support pagination.
- Thêm hàm `increase_reply_count`: Dùng `$inc` atomic.

### C. Service (`app/services/comment_service.py`)
- Logic `create_comment`:
    - Kiểm tra `post_id` tồn tại.
    - Nếu có `parent_id`: Kiểm tra comment cha tồn tại không.
    - Insert comment mới.
    - Chạy background task (hoặc await) để update `reply_count` cho comment cha và `comments_count` cho bài viết.

### D. Router (`app/api/v1/endpoints/comments.py`)
- Update `create_comment` để nhận `parent_id`.
- Thêm endpoint `get_comment_replies`.

---

## 4. Checklist triển khai

- [ ] **Schema**: Update `app/schemas/comment.py` (Uncomment `parent_id`, add `reply_count`).
- [ ] **Repository**:
    - [ ] Update `CommentRepository.create`.
    - [ ] Implement `CommentRepository.get_replies(parent_id, skip, limit)`.
    - [ ] Implement `CommentRepository.increase_reply_count(comment_id)`.
- [ ] **Service**:
    - [ ] Update logic `create_comment` để handle logic tăng count 2 nơi (Post + Parent Comment).
    - [ ] Implement `get_replies_for_comment`.
- [ ] **API**:
    - [ ] Endpoint `POST /` (Test case reply).
    - [ ] Endpoint `GET /{id}/replies`.
- [ ] **Performance**: Đảm bảo đã tạo Index trong MongoDB (`setup_mongo_indexes.py`).

