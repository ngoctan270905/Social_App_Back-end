# Kế hoạch & Triển khai Trang Cá Nhân (User Profile)

Tài liệu này mô tả kiến trúc và cách thức triển khai trang cá nhân cho người dùng (bao gồm chính mình và người khác) trong hệ thống My Social App.

## 1. Kiến Trúc Tổng Quan

Để tối ưu hiệu suất và trải nghiệm người dùng, việc hiển thị trang cá nhân được chia thành **2 luồng dữ liệu riêng biệt**, gọi 2 API khác nhau:

### Luồng 1: Thông tin Profile (Profile Info)
*   **Mục đích:** Lấy các thông tin tĩnh/ít thay đổi như Tên hiển thị, Avatar, Ảnh bìa, Tiểu sử (Bio), Số lượng bạn bè...
*   **Thời điểm gọi:** Chỉ gọi **1 lần duy nhất** khi trang vừa được tải (Component Mount).
*   **API Endpoint:** `GET /api/v1/users/{user_id}`
*   **Ưu điểm:** Giúp phần Header của trang load ngay lập tức, không phải chờ tải xong danh sách bài viết nặng nề.

### Luồng 2: Danh sách Bài viết (User Posts)
*   **Mục đích:** Lấy danh sách các bài viết do người dùng đó đăng.
*   **Thời điểm gọi:** Gọi ngay sau khi trang load và gọi tiếp khi người dùng cuộn xuống dưới (Infinite Scroll).
*   **API Endpoint:** `GET /api/v1/profiles/{user_id}/posts?cursor=...&limit=5`
*   **Ưu điểm:** Tải dữ liệu từng phần (Pagination), giảm tải cho Server và Client.

---

## 2. Chi Tiết Thay Đổi Backend

### 2.1. Service (`user_service.py`)
Thêm phương thức `get_user_by_id` để lấy thông tin public của user từ Database.
*   **Input:** `user_id` (string)
*   **Logic:**
    *   Tìm user trong collection `users` theo `_id`.
    *   Nếu không thấy -> Trả lỗi 404.
    *   Nếu thấy -> Loại bỏ trường `hashed_password` (bảo mật).
    *   Chuyển `_id` (ObjectId) thành `id` (string).
*   **Output:** Dictionary chứa thông tin user.

### 2.2. API Endpoint (`users.py`)
Thêm route mới để Frontend gọi:
```python
@router.get("/{user_id}", response_model=UserResponse)
async def get_user_details(user_id: str, ...):
    return await user_service.get_user_by_id(user_id)
```

---

## 3. Chi Tiết Thay Đổi Frontend

### 3.1. Routing (`AppRouter.tsx`)
Sử dụng một đường dẫn thống nhất cho cả bản thân và người khác:
*   **Route:** `/profile/:userId`
*   **Component:** `UserProfilePage`

### 3.2. Logic Trang (`UserProfilePage.tsx`)
Trang này đóng vai trò "Nhạc trưởng" điều phối dữ liệu:
1.  **Lấy ID:** Sử dụng `useParams()` để lấy `userId` từ URL.
2.  **Xác định Chính chủ:** So sánh `userId` trên URL với `currentUser.id` trong Context.
    *   `const isOwnProfile = currentUser.id === userId;`
3.  **Gọi API Profile:** Sử dụng `useEffect` để fetch thông tin user từ `GET /api/v1/users/{userId}` và lưu vào state (`userInfo`).
4.  **Render Giao diện:**
    *   Truyền `isOwnProfile` xuống các component con (`ProfileCover`, `ProfileInfo`) để ẩn/hiện các nút chức năng (Sửa vs Kết bạn).
    *   Truyền `userInfo` (Tên, Avatar...) vào để hiển thị.
    *   Truyền `userId` vào component `ProfilePostList`.

### 3.3. Component Bài Viết (`ProfilePostList.tsx`)
*   Nhận prop `userId`.
*   Gọi API `GET /api/v1/profiles/{userId}/posts` thay vì gọi API lấy Newsfeed chung.

### 3.4. Điều hướng (`PostCard.tsx`)
Khi click vào Avatar hoặc Tên người đăng bài:
*   Luôn điều hướng đến `/profile/{author_id}`.
*   Hệ thống Router sẽ tự render trang Profile tương ứng.

---

## 4. Các bước tiếp theo (To-Do)
1.  [Backend] Implement `get_user_by_id` trong `UserService`.
2.  [Backend] Đăng ký endpoint `GET /{user_id}`.
3.  [Frontend] Tạo service `getUserById(id)` trong `userService.ts`.
4.  [Frontend] Cập nhật `UserProfilePage` để gọi service này và thay thế dữ liệu giả (placeholder).
