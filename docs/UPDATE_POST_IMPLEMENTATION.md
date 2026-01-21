# Hướng dẫn triển khai tính năng cập nhật bài viết (Update Post) - Đầy đủ Media

Tài liệu này mô tả các bước để hoàn thiện tính năng cập nhật bài viết, bao gồm cả việc **thêm ảnh mới** và **xóa ảnh cũ**.

## 1. Cập nhật Service (`app/services/news_service.py`)

Logic xử lý cần phức tạp hơn để xử lý danh sách media.

```python
# app/services/news_service.py

    # Logic update post ================================================================================================
    async def update_post(
        self, 
        post_id: str, 
        user_id: str,
        content: Optional[str] = None,
        privacy: Optional[str] = None,
        keep_media_ids: List[str] = [], # Danh sách ID ảnh cũ muốn giữ lại
        new_files: List[UploadFile] = [] # Danh sách ảnh mới muốn thêm
    ) -> PostCreateResponse:
        
        # 1. Lấy thông tin bài viết hiện tại
        post = await self.post_repo.get_by_id(post_id)
        if not post:
            raise NotFoundError()

        # 2. Check quyền
        if str(post["user_id"]) != user_id:
            raise ForbiddenError()

        # 3. Xử lý Media
        current_media_ids = [str(m) for m in post.get("media_ids", [])]
        
        # 3.1: Lọc ra danh sách ID cuối cùng từ những ảnh cũ
        # Chỉ giữ lại những ID có trong danh sách keep_media_ids gửi lên
        # Nếu frontend gửi keep_media_ids rỗng -> Xóa hết ảnh cũ
        final_media_ids = []
        for mid in current_media_ids:
            if mid in keep_media_ids:
                final_media_ids.append(ObjectId(mid))
        
        # 3.2: Upload ảnh mới (nếu có)
        if new_files:
            new_medias = await self.media_service.upload_many_media_and_save(
                files=new_files,
                folder="posts",
            )
            for m in new_medias:
                final_media_ids.append(ObjectId(m.id))

        # 4. Chuẩn bị dữ liệu update
        update_data = {
            "updated_at": datetime.utcnow(),
            "media_ids": final_media_ids # Cập nhật danh sách ID mới
        }
        
        if content is not None:
            update_data["content"] = content
        if privacy is not None:
            update_data["privacy"] = privacy

        # 5. Thực hiện update
        post = await self.post_repo.update(update_data, post_id)

        # 6. Lấy thông tin media đầy đủ để trả về
        media_public = []
        if final_media_ids:
            medias = await self.media_repo.get_by_ids(final_media_ids)
            media_public = [
                MediaPublic(
                    id=str(m["_id"]),
                    type=m["type"],
                    url=m["url"],
                )
                for m in medias
            ]

        return PostCreateResponse(
            _id=post["_id"],
            content=post["content"],
            privacy=post["privacy"],
            media=media_public,
            created_at=post["created_at"]
        )
```

## 2. Cập nhật Endpoint (`app/api/v1/endpoints/news.py`)

Chuyển endpoint sang dùng `Form` và `File` hoàn toàn để hỗ trợ upload. Không dùng Pydantic model (`PostUpdate`) trong Body nữa mà dùng Form parameters.

```python
# app/api/v1/endpoints/news.py

@router.patch("/{post_id}", response_model=ResponseModel[PostCreateResponse], summary="Cập nhật bài viết (Full Media)")
async def update_post(
    post_id: str,
    content: Optional[str] = Form(None),
    privacy: Optional[PostType] = Form(None),
    keep_media_ids: Optional[List[str]] = Form(None), # Nhận list ID dạng form data
    files: Optional[List[UploadFile]] = File(None),   # Nhận file mới
    service: PostService = Depends(get_post_service),
    current_user: dict = Depends(get_current_user)
):
    # Xử lý trường hợp list gửi lên là None
    if keep_media_ids is None:
        keep_media_ids = []

    updated_post = await service.update_post(
        post_id=post_id,
        user_id=current_user['_id'],
        content=content,
        privacy=privacy,
        keep_media_ids=keep_media_ids,
        new_files=files if files else []
    )
    
    return ResponseModel(
        data=updated_post, 
        message="Cập nhật bài viết thành công"
    )
```

## 3. Lưu ý cho Frontend

Khi gọi API này:
- Phải dùng `Content-Type: multipart/form-data`.
- **Giữ ảnh cũ:** Gửi danh sách `keep_media_ids`. Ví dụ bài có ảnh A, B. User xóa ảnh B -> Gửi `keep_media_ids=["ID_Cua_A"]`.
- **Xóa hết ảnh cũ:** Gửi `keep_media_ids=[]` (hoặc không gửi, tùy logic backend handle mặc định).
- **Thêm ảnh mới:** Gửi file vào field `files`.
- **Sửa nội dung:** Gửi `content`.

Ví dụ Form Data:
```
content: "Nội dung mới đã sửa"
privacy: "public"
keep_media_ids: "65a123..."
keep_media_ids: "65b456..." 
files: (binary data file 1)
files: (binary data file 2)
```