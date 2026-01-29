# Tài liệu Luồng Xử lý (Flow) - Profile Feature

Tài liệu này mô tả chi tiết luồng dữ liệu của các API liên quan đến Profile trong hệ thống.

## 1. Biểu đồ Sequence (Sequence Diagram)

Bạn có thể copy đoạn code dưới đây vào [Mermaid.live](https://mermaid.live/) để xem biểu đồ.

```mermaid
sequenceDiagram
    autonumber
    actor User as User (Client)
    participant API as Profile Controller
    participant Service as UserProfile Service
    participant Upload as Upload Service
    participant Cloud as Cloudinary
    participant DB as MongoDB (Repos)

    rect rgb(230, 240, 255)
        note right of User: FLOW 1: UPLOAD & UPDATE AVATAR
        User->>API: PATCH /api/v1/profiles/avatar (File Image)
        activate API
        API->>Service: update_profile_avatar(file, user_id)
        activate Service
        
        Service->>Upload: upload_media(file, folder="avatars")
        activate Upload
        Upload->>Cloud: Upload Image
        Cloud-->>Upload: Return URL, Public ID
        Upload-->>Service: Return Media Data
        deactivate Upload

        Service->>DB: MediaRepo.create(media_data) (Lưu Media mới)
        DB-->>Service: Return Media Document (có ID)
        
        Service->>DB: UserProfileRepo.update_avatar(user_id, media_id)
        DB-->>Service: Return Updated Profile

        Service-->>API: Return UpdateProfileAvatar (URL, ID)
        deactivate Service
        API-->>User: 201 Created + Avatar Info
        deactivate API
    end

    rect rgb(255, 250, 230)
        note right of User: FLOW 2: GET USER PROFILE (Detail)
        User->>API: GET /api/v1/profiles/{user_id}
        activate API
        API->>Service: get_profile_by_id(user_id)
        activate Service
        
        Service->>DB: UserRepo.get_by_id(user_id) (Check tồn tại)
        alt User Not Found
            DB-->>Service: Null
            Service-->>API: Raise NotFoundError
            API-->>User: 404 Not Found
        end
        
        Service->>DB: UserProfileRepo.get_by_user_id(user_id)
        DB-->>Service: Return Profile Doc
        
        opt Profile has Avatar
            Service->>DB: MediaRepo.get_by_id(avatar_id)
            DB-->>Service: Return Media Doc (URL)
        end
        
        Service-->>API: Return UserProfileDetail
        deactivate Service
        API-->>User: 200 OK + Profile Data (Name, Avatar URL...)
        deactivate API
    end

    rect rgb(230, 255, 230)
        note right of User: FLOW 3: GET USER POSTS
        User->>API: GET /api/v1/profiles/{user_id}/posts
        activate API
        API->>Service: PostService.get_user_posts(user_id)
        activate Service
        Service->>DB: Query Posts by Author ID
        DB-->>Service: Return List Posts
        Service-->>API: Return List Data
        deactivate Service
        API-->>User: 200 OK + List Posts
        deactivate API
    end
```

## 2. Giải thích chi tiết các bước

### 2.1. Upload & Cập nhật Avatar (PATCH /avatar)
*   **Input**: File hình ảnh (multipart/form-data) và Access Token.
*   **Logic**:
    1.  Backend nhận file, chuyển cho `UploadService` để đẩy lên Cloudinary trong folder `avatars`.
    2.  Sau khi có URL từ Cloudinary, thông tin được lưu vào collection `media`.
    3.  Lấy ID của media mới tạo, cập nhật vào field `avatar` của User tương ứng trong collection `user_profiles`.
*   **Output**: Trả về thông tin media (ID, URL, Type) để Frontend cập nhật UI ngay lập tức.

### 2.2. Lấy thông tin Profile (GET /{user_id})
*   **Logic**:
    1.  Kiểm tra user có tồn tại trong hệ thống không qua `UserRepo`.
    2.  Truy vấn thông tin cơ bản (display_name, ...) từ `UserProfileRepo`.
    3.  Nếu có `avatar_id`, tiếp tục truy vấn sang `MediaRepo` để lấy URL ảnh thật.
*   **Output**: Profile hoàn chỉnh bao gồm thông tin hiển thị và ảnh đại diện.

### 2.3. Lấy danh sách bài viết (GET /{user_id}/posts)
*   **Logic**:
    1.  Sử dụng `PostService` để lọc tất cả bài viết có `author_id` khớp với `user_id`.
    2.  Hỗ trợ phân trang (cursor/limit) để tối ưu hiệu năng.
