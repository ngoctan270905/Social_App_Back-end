from datetime import datetime, timezone
from typing import Optional, Dict, Any
import redis.asyncio as redis
import time
from jose import jwt, JWTError
import random
from pydantic import EmailStr
from app.exceptions.auth import EmailAlreadyExistsError, UserNotFoundError, XacMinhError, OTPKhongTonTai, \
    OTPKhongChinhXac, XacMinhEmail, Ban, UserNotFoundErrorMail, RefreshTokenNotFoundError, UserInvalidForToken
from app.repositories.user_profile_repository import UserProfileRepository
from app.services.blacklist_service import BlacklistService
from fastapi import HTTPException, status, Request, Response, BackgroundTasks
from app.schemas.auth import UserRegister, Token, UserRegisterResponse
from app.repositories.user_repository import UserRepository
from app.core.security import verify_password,hash_password,create_access_token, create_scoped_token, verify_scoped_token
from app.core.email import send_verification_email, send_password_reset_otp_email
from app.services.token_service import TokenService
from app.core.config import settings



class AuthService:

    def __init__(self, user_repo: UserRepository,
                       token_service: TokenService,
                       user_profile_repo: UserProfileRepository,
                       redis_client: redis.Redis):
        self.user_profile_repo = user_profile_repo
        self.user_repo = user_repo
        self.token_service = token_service
        self.redis_client = redis_client


    # Logic đăng kí tài khoản ==========================================================================================
    async def register(self, user_data: UserRegister, background_tasks: BackgroundTasks) -> UserRegisterResponse:

        normalized_email = str(user_data.email).strip().lower()

        # 1. Kiểm tra email
        if await self.user_repo.get_by_email(normalized_email):
            raise EmailAlreadyExistsError()

        # 2. Hash password
        hashed_pwd = hash_password(user_data.password)

        # 3. Dữ liệu cho bảng User
        user_auth_data = {
            "email": normalized_email,
            "password": hashed_pwd,
            "status": "pending",
            "email_verified": False,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }

        # 4. LƯU
        try:
            # 1: Tạo User trước để lấy ID
            created_user = await self.user_repo.create(user_auth_data)
            user_id = created_user["_id"]

            # 2: Tạo Profile sử dụng ID vừa lấy
            dob = datetime(user_data.year, user_data.month, user_data.day)

            user_profile_data = {
                "user_id": user_id,
                "first_name": user_data.first_name,
                "last_name": user_data.last_name,
                "display_name": f"{user_data.last_name} {user_data.first_name}".strip(),
                "date_of_birth": dob,
                "gender": user_data.gender,
                "avatar": None,
                "cover_photo": None,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }

            await self.user_profile_repo.create(user_profile_data)

            # 5. Xử lý OTP
            otp_code = "".join([str(random.randint(0, 9)) for _ in range(6)])
            await self.redis_client.setex(
                f"auth:otp:email:{normalized_email}", 300, otp_code
            )

            background_tasks.add_task(
                send_verification_email,
                email_to=normalized_email,
                otp_code=otp_code,
                name=user_data.first_name
            )

            return UserRegisterResponse(email=normalized_email)


        except Exception as e:
            raise e



    # Logic xác minh email =============================================================================================
    async def verify_email(self, email: str, otp: str) -> UserRegisterResponse:
        key = f"auth:otp:email:{email}"
        stored_otp = await self.redis_client.get(key)

        # 2. Kiểm tra tính hợp lệ của OTP
        if not stored_otp:
            raise OTPKhongTonTai()

        if stored_otp != otp:
            raise OTPKhongChinhXac()

        user = await self.user_repo.get_by_email(email)
        if not user:
            raise UserNotFoundError()

        if user.get("email_verified"):
            raise XacMinhError()

        update_data = {
            "status": "active",
            "email_verified": True
        }
        updated_user = await self.user_repo.update(user_id=user["_id"], user_data=update_data)
        await self.redis_client.delete(key)
        return UserRegisterResponse(**updated_user)



    # Logic gửi lại mã OTP =============================================================================================
    async def resend_verification_email(self, email: str, background_tasks: BackgroundTasks):
        # 1. Kiểm tra user tồn tại
        user = await self.user_repo.get_by_email(email)
        if not user:
            raise UserNotFoundError()

        # 2. Kiểm tra đã kích hoạt chưa
        if user.get("email_verified"):
            raise XacMinhError()

        # 3. Sinh OTP mới
        otp_code = "".join([str(random.randint(0, 9)) for _ in range(6)])

        # 4. Lưu vào Redis (Ghi đè OTP cũ -> Tự động revoke OTP cũ)
        await self.redis_client.setex(
            f"auth:otp:email:{email}",
            300,
            otp_code
        )

        # 5. Gửi email background
        background_tasks.add_task(
            send_verification_email,
            email_to=email,
            otp_code=otp_code,
            name=user.get("first_name", "User")
        )

        return {"message": "Đã gửi lại mã xác minh. Vui lòng kiểm tra email."}



    # Logic quên mật khẩu ==============================================================================================
    async def forgot_password(self, email: str, background_tasks: BackgroundTasks):
        user = await self.user_repo.get_by_email(email)
        if not user:
            return {"message": "Đã gửi mã xác nhận, vui lòng kiểm tra email"}

        otp_code = "".join([str(random.randint(0, 9)) for _ in range(6)])

        await self.redis_client.setex(
            f"auth:otp:forgot-password:{user['email']}",
            300,
            otp_code
        )
        background_tasks.add_task(
            send_password_reset_otp_email,
            email_to=user['email'],
            otp_code=otp_code,
            name=user.get('first_name', 'User')
        )


        return {"message": "Đã gửi mã khôi phục mật khẩu, vui lòng kiểm tra email"}



    # Logic xác minh OTP ===============================================================================================
    async def verify_forgot_password_otp(self, email: str, otp: str):
        key = f"auth:otp:forgot-password:{email}"
        # 1. Lấy OTP từ Redis
        stored_otp = await self.redis_client.get(key)

        # 2. Kiểm tra
        if not stored_otp:
            raise OTPKhongTonTai()

        if stored_otp != otp:
            raise OTPKhongChinhXac()

        await self.redis_client.delete(key)

        # 4. Tạo Token reset password
        password_reset_token = create_scoped_token(
            subject=email,
            scope="password_reset",
            expires_in_minutes=10
        )
        print(f"test {password_reset_token}")

        return {"reset_token": password_reset_token}



    # Logic reset mật khẩu =============================================================================================
    async def reset_password(self, token: str, new_password: str) -> UserRegisterResponse:
        email = await verify_scoped_token(token, required_scope="password_reset")

        user = await self.user_repo.get_by_email(str(email))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        hashed_password = hash_password(new_password)
        user['password'] = hashed_password
        updated_user = await self.user_repo.update(user['_id'], {'password': hashed_password})
        return UserRegisterResponse(**updated_user)



    # Logic đăng nhập ==================================================================================================
    async def login(self, *, response: Response, token_service: TokenService, email: str, password: str) -> Token:
        print(f"Đi vào đây")
        user = await self.user_repo.get_by_email(email)
        if not user:
            raise UserNotFoundErrorMail()

        # tạo biến trước để kiểm tra mật khẩu là False
        is_password_correct = False
        if user:
            is_password_correct = verify_password(password, user['password'])

        # nếu user ko tồn tại hoặc password sai
        if not user or not is_password_correct:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Tài khoản hoặc mật khẩu không chính xác!",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if user['status'] == "pending" or not user.get('email_verified', False):
            raise XacMinhEmail()
        elif user['status'] == "suspended":
            raise Ban()

        # Nếu user tồn tại, mật khẩu đúng
        # Thì gọi hàm create_access_token ở security.py để tạo access token
        access_token = create_access_token(
            data={"sub": str(user['_id']), "email": user['email']}
        )
        # Gọi tiếp services để xử lí thêm refresh_token
        refresh_token = await token_service.create_refresh_token(user=user)

        # Đặt refresh token về cooki httpOnly
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=settings.ENVIRONMENT == "production",
            samesite="lax",
            max_age=settings.REFRESH_TOKEN_EXPIRE_SECONDS
        )

        return Token(access_token=access_token)



    # Hàm xử lí làm mới token ==========================================================================================
    async def refresh_user_tokens(self, refresh_token: Optional[str], response: Response) -> Token:
        if not refresh_token:
            raise RefreshTokenNotFoundError()

        # Xác minh refresh token
        user_id = await self.token_service.verify_refresh_token(refresh_token)

        # Thu hồi token
        await self.token_service.revoke_refresh_token(refresh_token)

        # lấy user
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise UserInvalidForToken()

        # Create new tokens
        new_access_token = create_access_token(
            data={"sub": str(user['_id']), "email": user['email']}
        )
        new_refresh_token = await self.token_service.create_refresh_token(user=user)

        # Set cookie
        response.set_cookie(
            key="refresh_token",
            value=new_refresh_token,
            httponly=True,
            secure=settings.ENVIRONMENT == "production",
            samesite="lax",
            max_age=30 * 24 * 60 * 60
        )

        return Token(access_token=new_access_token)



    # hàm xử lí logic đăng xuất ========================================================================================
    async def logout(
            self, *,
            response: Response,
            token_service: TokenService,
            redis_client: redis.Redis,
            access_token: str,
            refresh_token: Optional[str]
    ) -> dict:

        # Thêm token vào ds đen
        try:
            # giải mã token lấy jti exp
            payload = jwt.decode(
                access_token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
                options={"verify_signature": False}
            )
            jti = payload.get("jti")  # mã định danh
            exp = payload.get("exp")  # thời gian hết hạn
            user_id = payload.get("sub")

            if jti and exp:
                blacklist_service = BlacklistService(redis_client)
                # số giây token còn sống : thời gian hết hạn - tg hiện tại
                ttl = exp - int(time.time())

                if ttl > 0:  # chỉ thêm v àoblacklist nếu token chưa hết hạn
                    await blacklist_service.add_to_blacklist(jti, ttl, user_id=user_id, exp=exp)

        except Exception as e:
            print(f"Lỗi khi thêm vào black list: {e}")

        # revoke refresh token (nếu có)
        if refresh_token:
            try:
                await token_service.revoke_refresh_token(refresh_token)
            except HTTPException as e:
                if e.status_code not in [status.HTTP_401_UNAUTHORIZED, status.HTTP_404_NOT_FOUND]:
                    raise e

        # Luôn xóa cookie
        response.delete_cookie(key="refresh_token")

        return {"message": "Bạn đã logout thành công"}


    # async def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
    #     user = await self.user_repo.get_by_username(username)
    #     if not user:
    #         return None
    #     if not verify_password(password, user["hashed_password"]):
    #         return None
    #
    #     user["_id"] = str(user["_id"])
    #     return user
