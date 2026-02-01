# Kế hoạch triển khai API Thêm Bình Luận (Create Comment)

## 1. Phân tích Database (MongoDB)

Do tính chất của comment trong mạng xã hội là số lượng lớn (High Volume) và có thể fan-out (nhiều người đọc), ta sẽ tách Comments ra một Collection riêng thay vì embed vào Post.

### Collection: `comments`

| Field | Type | Description | Index |
| :--- | :--- | :--- | :--- |
| `_id` | ObjectId | Primary Key | Default |
| `post_id` | ObjectId | Reference to `posts` | **Indexed** (để query comment theo bài viết) |
| `user_id` | ObjectId | Reference to `users` | |
| `content` | String | Nội dung bình luận | |
| `media` | Array | (Optional) Danh sách ảnh/video đính kèm | |
| `created_at` | DateTime | Thời gian tạo | **Indexed** (để sort timeline) |
| `updated_at` | DateTime | Thời gian cập nhật | |
| `parent_id` | ObjectId | (Optional) Hỗ trợ trả lời bình luận (Reply) | |

### Collection Update: `posts`
Cần thêm field `comments_count` vào collection `posts` để tối ưu hiệu năng hiển thị (tránh count documents mỗi lần load feed).
- Update: Dùng `$inc` khi thêm/xóa comment.

---

## 2. Cấu trúc Source Code

Tuân thủ kiến trúc Layered Architecture hiện có:

### A. Schema (`app/schemas/comment.py`)
- `CommentCreate`: Validate input (content, post_id).
- `CommentResponse`: Định dạng dữ liệu trả về cho Client.

### B. Repository (`app/repositories/comment_repository.py` & update `posts_repository.py`)
- `CommentRepository.create`: Insert comment vào DB.
- `PostRepository.increase_comment_count`: Atomic update (`$inc`) số lượng comment.

### C. Service (`app/services/comment_service.py`)
- Validate `post_id` tồn tại.
- Gọi Repo tạo comment.
- Gọi Repo update count (đảm bảo atomic hoặc handle failure - ở mức MVP sẽ dùng `await` tuần tự để an toàn).

### D. API Endpoint (`app/api/v1/endpoints/comments.py`)
- `POST /api/v1/comments/`: Endpoint tạo bình luận.

### E. Router (`app/api/v1/router.py`)
- Include router mới.

---

## 3. Checklist triển khai (Tuân thủ GEMINI.md)

- [ ] **Schema Definition**: Tạo file `app/schemas/comment.py`.
- [ ] **Repository Implementation**:
    - Tạo `app/repositories/comment_repository.py`.
    - Thêm method `increase_comment_count` vào `app/repositories/posts_repository.py`.
- [ ] **Service Implementation**:
    - Tạo `app/services/comment_service.py`.
    - Logic: Check Post Exists -> Create Comment -> Inc Count.
    - **Lưu ý GEMINI.md**: Không dùng blocking I/O, không query sync.
- [ ] **API Endpoint**:
    - Tạo `app/api/v1/endpoints/comments.py`.
- [ ] **Dependency Injection**:
    - Cập nhật `app/api/deps.py` để provide `CommentService`.
- [ ] **Wiring**:
    - Register router trong `app/api/v1/router.py`.

