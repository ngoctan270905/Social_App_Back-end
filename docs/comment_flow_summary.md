Dưới đây là tóm tắt luồng xử lý tính năng bình luận và trả lời bình luận, cùng với cơ chế thông báo thời gian thực, dựa trên cấu trúc schema hiện tại (`reply_to_comment_id` và `root_id`).

**Lưu ý về thuật ngữ:** Tài liệu `COMMENT_FLOW.md` gốc có thể sử dụng `parent_id`, nhưng việc triển khai thực tế dựa trên `app/schemas/comment.py` cho thấy các trường `reply_to_comment_id` (ID của bình luận được trả lời trực tiếp) và `root_id` (ID của bình luận gốc trong một chuỗi) được sử dụng để quản lý cấu trúc bình luận. Tóm tắt này sẽ tuân theo thuật ngữ của schema.

**1. Tạo Bình Luận Mới**
Khi người dùng tạo một bình luận mới trên một bài viết, client gửi POST request bao gồm `post_id` (ID bài viết) và `content` (nội dung bình luận). API Server xác thực request, lưu bình luận vào collection `comments`. Bình luận này sẽ có `reply_to_comment_id` là `null` và `root_id` là `null` (hoặc cùng `_id` của chính nó nếu là bình luận gốc đầu tiên của một chuỗi). Đồng thời, server cập nhật `comments_count` của bài viết tương ứng. Sau đó, một tiến trình nền sẽ được kích hoạt để gửi thông báo "NEW_COMMENT" qua WebSocket đến chủ bài viết nếu người bình luận không phải là chủ bài viết. Cuối cùng, API Server trả về thông tin chi tiết của bình luận vừa tạo.

**2. Trả Lời Bình Luận**
Khi người dùng phản hồi một bình luận hiện có, client gửi POST request chứa `post_id`, `content` và `reply_to_comment_id` (ID của bình luận mà người dùng đang trả lời trực tiếp). API Server xác thực request, lưu bình luận trả lời vào collection `comments`. Bình luận trả lời sẽ có `reply_to_comment_id` là ID của bình luận được trả lời và `root_id` sẽ được thiết lập là `root_id` của bình luận được trả lời (hoặc `_id` của bình luận được trả lời nếu nó là bình luận gốc của chuỗi). Server cũng tăng `reply_count` của bình luận được trả lời và tăng `comments_count` của bài viết gốc. Một tiến trình nền sẽ gửi thông báo "NEW_REPLY" qua WebSocket đến chủ bình luận được trả lời. API Server trả về thông tin chi tiết của bình luận trả lời.

**3. Đọc Bình Luận và Trả Lời**
*   **Lấy Bình Luận Gốc:** Client gửi GET request để lấy danh sách các bình luận gốc của một bài viết (ví dụ: `/api/v1/posts/{post_id}/comments`). API Server truy vấn collection `comments` để tìm các document có `post_id` khớp và `reply_to_comment_id` là `null`. Kết quả được sắp xếp, phân trang và populate thông tin người dùng/media liên quan.
*   **Lấy Các Phản Hồi:** Khi người dùng muốn xem các phản hồi cho một bình luận cụ thể (có thể là một bình luận gốc hoặc một phản hồi khác), client gửi GET request (ví dụ: `/api/v1/comments/{comment_id}/replies`). API Server truy vấn `comments` để tìm các document có `reply_to_comment_id` khớp với `comment_id` được yêu cầu, hoặc sử dụng `root_id` để lấy toàn bộ chuỗi phản hồi. Kết quả được sắp xếp, phân trang và populate dữ liệu.
API Server trả về danh sách các bình luận hoặc phản hồi tương ứng.

**4. Thông Báo Thời Gian Thực**
Cơ chế này đẩy thông báo liên quan đến bình luận/trả lời đến người dùng ngay lập tức qua WebSocket. Khi người dùng đăng nhập, client thiết lập kết nối WebSocket với server. Server xác thực và lưu trữ kết nối. Khi một sự kiện bình luận/trả lời xảy ra và cần thông báo, `NotificationService` tạo bản ghi thông báo vào MongoDB. Sau đó, nó sử dụng `ConnectionManager` để tìm và gửi JSON payload thông báo qua WebSocket đến tất cả các kết nối của `user_id` mục tiêu. JSON payload sẽ bao gồm các thông tin như `type` (NEW_COMMENT, NEW_REPLY) và `entity_ref` chứa `post_id`, `comment_id` (ID của bình luận/phản hồi mới), `reply_to_comment_id`, và `root_id` để hỗ trợ deep linking chính xác. Client nhận payload và hiển thị thông báo.

**Tinh thần chung (Theo GEMINI.md)**
*   **Tránh Sequential I/O trong Loop:** Đảm bảo các hoạt động đọc/ghi cơ sở dữ liệu và gửi WebSocket không chặn luồng chính và được tối ưu hóa.
*   **Không Blocking trong Async:** Các tác vụ nặng (như cập nhật count, gửi thông báo) được xử lý trong background hoặc bằng cách không đồng bộ để không làm lag toàn bộ server.
*   **Fan-out có kiểm soát:** Gửi thông báo WebSocket tới nhiều thiết bị/người dùng được quản lý để tránh tự tấn công từ chối dịch vụ (DDoS).
*   **Idempotent:** Các thao tác cập nhật count cần được xem xét để đảm bảo tính idempotent nếu có retry (ví dụ: sử dụng transactions hoặc `$inc` an toàn).