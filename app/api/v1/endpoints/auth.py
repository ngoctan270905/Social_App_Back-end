from typing import Annotated, Optional, Dict

import redis.asyncio as redis
from fastapi import APIRouter, Depends, status, Response, Cookie, HTTPException, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import get_auth_service, get_token_service, get_user_repository
from app.core.dependencies import get_current_user, oauth2_scheme
from app.core.redis_client import get_redis_client
from app.core.security import create_access_token
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    UserRegister,
    Token,
    UserResponse,
    EmailVerificationRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest, UserRegisterResponse, ResendVerificationRequest, VerifyForgotPasswordRequest, UserMeResponse
)
from app.schemas.response import ResponseModel
from app.services.auth_service import AuthService
from app.services.token_service import TokenService

router = APIRouter()

# ==================== Đăng ký =========================================================================================
@router.post("/register", response_model=ResponseModel[UserRegisterResponse],
             status_code=status.HTTP_201_CREATED, summary="Đăng ký")
async def register(
        user_data: UserRegister,
        background_tasks: BackgroundTasks,
        auth_service: Annotated[AuthService, Depends(get_auth_service)]
):
    user_register = await auth_service.register(user_data, background_tasks)
    return ResponseModel(data=user_register, message="Đăng ký user thành công")



# ==================== Xác minh Email ==================================================================================
@router.post("/verify-email", response_model=ResponseModel[UserRegisterResponse], summary="Xác minh Email")
async def verify_email(
    request: EmailVerificationRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)]
):
    user_verify_email = await auth_service.verify_email(str(request.email), request.otp)
    return ResponseModel(data=user_verify_email, message="Xác thực email thành công")



# Gửi lại mã xác minh ==================================================================================================
@router.post("/resend-verification", status_code=status.HTTP_200_OK, summary="Gửi lại mã xác minh")
async def resend_verification(
    request: ResendVerificationRequest,
    background_tasks: BackgroundTasks,
    auth_service: Annotated[AuthService, Depends(get_auth_service)]
):
    return await auth_service.resend_verification_email(str(request.email), background_tasks)



# ==================== Quên mật khẩu ===================================================================================
@router.post("/forgot-password", status_code=status.HTTP_200_OK, summary="Quên mật khẩu")
async def forgot_password(
    request: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    auth_service: Annotated[AuthService, Depends(get_auth_service)]
):
    user_forgot_password = await auth_service.forgot_password(str(request.email), background_tasks)
    return user_forgot_password



# Xác thực OTP đổi mật khẩu ============================================================================================
@router.post("/verify-forgot-password-otp", status_code=status.HTTP_200_OK, summary="Xác thực OTP quên mật khẩu")
async def verify_forgot_password(
    request: VerifyForgotPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    return await auth_service.verify_forgot_password_otp(request.email, request.otp)



# Đổi mật khẩu =========================================================================================================
@router.post("/reset-password", response_model=ResponseModel[UserRegisterResponse], summary="Đổi mật khẩu")
async def reset_password(
    request: ResetPasswordRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)]
):
    user_reset_password = await auth_service.reset_password(request.token, request.new_password)
    return ResponseModel(data=user_reset_password, message="Đổi mật khẩu thành công")



# ==================== LOGIN ===========================================================================================
@router.post("/login", response_model=Token, summary="Đăng nhập")
async def login(
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    token_service: Annotated[TokenService, Depends(get_token_service)]
):
    user_login = await (auth_service.login(
        response=response,
        token_service=token_service,
        email=form_data.username,
        password=form_data.password))
    return user_login


# ==================== REFRESH TOKEN ===================================================================================
@router.post("/refresh", response_model=ResponseModel[Token], summary="Làm mới Token")
async def refresh_token(
    response: Response,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    refresh_token: str = Cookie(None)
):
    token = await auth_service.refresh_user_tokens(refresh_token, response)
    return ResponseModel(data=token, message="Refresh token thành công")



# ==================== GET USER INFO ===================================================================================
@router.get("/me", response_model=ResponseModel[UserMeResponse], summary="Lấy thông tin User")
async def get_current_user_info(
    current_user: dict = Depends(get_current_user)
):
    return ResponseModel(data=current_user, message="Lấy thông tin user thành công")



# ==================== LOGOUT ==========================================================================================
@router.post("/logout", status_code=status.HTTP_200_OK, summary="Đăng xuất")
async def logout(
    response: Response,
    current_user: Annotated[dict, Depends(get_current_user)],
    redis_client: Annotated[redis.Redis, Depends(get_redis_client)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    token_service: Annotated[TokenService, Depends(get_token_service)],
    token: Annotated[str, Depends(oauth2_scheme)],
    refresh_token: Optional[str] = Cookie(None),
):
    """
    Đăng xuất người dùng bằng cách:
    1. Vô hiệu hóa access token (thêm vào blacklist).
    2. Thu hồi refresh token (xóa khỏi DB và cookie).
    """
    return await auth_service.logout(
        response=response,
        token_service=token_service,
        redis_client=redis_client,
        access_token=token,
        refresh_token=refresh_token
    )


