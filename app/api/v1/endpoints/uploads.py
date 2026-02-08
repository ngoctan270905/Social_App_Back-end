# from typing import Annotated
# from fastapi import APIRouter, Depends, status, UploadFile, File, Form
#
# from app.schemas.media import MediaResponse, MediaCreate, MediaType
# from app.schemas.response import ResponseModel
# from app.services.media_service import MediaService
# from app.services.user_service import UserService
# from app.core.dependencies import get_current_user
# from app.api.deps import get_user_service, get_media_services
#
# router = APIRouter()
#
# @router.post(
#     "/",
#     response_model=ResponseModel[MediaResponse],
#     status_code=status.HTTP_201_CREATED,
#     summary="Upload Media"
# )
# async def upload_media(
#         file: UploadFile = File(...),
#         media_type: MediaType = Form(...),
#         service: MediaService = Depends(get_media_services),
#         user: dict = Depends(get_current_user)
# ):
#     folder = f"{media_type}s"
#
#     result = await service.upload(
#         file=file,
#         folder=folder,
#         media_type=media_type,
#         user_id=user['_id']
#     )
#
#     return {
#         "status": "success",
#         "message": "Upload ảnh thành công",
#         "data": result
#     }