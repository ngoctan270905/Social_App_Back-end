import uuid

from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import HTTPException, status
from app.core.config import settings
import redis.asyncio as redis
from app.services.blacklist_service import BlacklistService

# Cấu hình xử lí mật khẩu
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Hàm băm mật khẩu
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


# Hàm xác minh mật khẩu với password và hash_password
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# hàm tạo access token
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:

    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "scope": "access_token",
        "jti": str(uuid.uuid4()),
    })

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


# hàm tạo token dùng 1 lần
def create_scoped_token(subject: str, scope: str, expires_in_minutes: int) -> str:
    """
    Creates a generic JWT with a specific subject and scope.
    Used for things like email verification, password reset, etc.
    """
    expire = datetime.utcnow() + timedelta(minutes=expires_in_minutes)
    to_encode = {
        "exp": expire,
        "sub": subject,
        "scope": scope,
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


# Hàm xác thực JWT: signature, expiry, scope, blacklist
async def verify_scoped_token(
        token: str,
        required_scope: str,
        redis_client: Optional[redis.Redis] = None
) -> str:

    try:
        # Decode và verify token
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        # Kiểm tra subject
        subject = payload.get("sub")
        if not subject:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Kiểm tra scope
        token_scope = payload.get("scope")
        if token_scope != required_scope:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token scope. Required: {required_scope}, got: {token_scope}",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Kiểm tra blacklist (chỉ với access_token VÀ khi có redis_client)
        if required_scope == "access_token" and redis_client:
            jti = payload.get("jti")
            if not jti:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token không có JTI (JWT ID)",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            blacklist_service = BlacklistService(redis_client)

            if await blacklist_service.is_blacklisted(jti):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token đã bị thu hồi",
                    headers={"WWW-Authenticate": "Bearer"},
                )

        return subject

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Tạo JWT refresh token với scope 'refresh_token'.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({"exp": expire, "scope": "refresh_token"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt