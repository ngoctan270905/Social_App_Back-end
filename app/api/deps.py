from typing import Annotated
from fastapi import Depends
from app.repositories.author_repository import AuthorRepository
from app.repositories.book_repository import BookRepository
from app.repositories.news_repository import PostRepository
from app.repositories.media_repository import MediaRepository
from app.repositories.user_profile_repository import UserProfileRepository
from app.repositories.user_repository import UserRepository
from app.repositories.token_repository import TokenRepository
from app.repositories.category_repository import CategoryRepository
from app.services.auth_service import AuthService
from app.services.author_service import AuthorService
from app.services.book_service import BookService
from app.services.media_service import MediaService
from app.services.news_service import PostService
from app.services.notification_service import NotificationService
from app.services.upload_service import UploadService
from app.services.user_profile_service import UserProfileService
from app.services.user_service import UserService
from app.services.token_service import TokenService
from app.services.category_service import CategoryService
from app.core.redis_client import get_redis_client
import redis.asyncio as redis

def get_media_repository() -> MediaRepository:
    return  MediaRepository()

def get_post_repository() -> PostRepository:
    return PostRepository()

def get_user_profile_repository() -> UserProfileRepository:
    return UserProfileRepository()

# Dependency để lấy CategoryRepository
def get_category_repository() -> CategoryRepository:
    return CategoryRepository()


# # Dependency để lấy AuthorRepository
def get_author_repository() -> AuthorRepository:
    return AuthorRepository()


# Dependency để lấy BookRepository
def get_book_repository() -> BookRepository:
    return BookRepository()


# Dependency để lấy UserRepository
def get_user_repository() -> UserRepository:
    return UserRepository()


# Dependency để lấy TokenRepository
def get_token_repository() -> TokenRepository:
    return TokenRepository()


# Dependency để lấy TokenService
def get_token_service(
    token_repo: Annotated[TokenRepository, Depends(get_token_repository)]
) -> TokenService:
    return TokenService(token_repo)


# Dependency để lấy AuthService
def get_auth_service(
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
    user_profile_repo: Annotated[UserProfileRepository, Depends(get_user_profile_repository)],
    token_service: Annotated[TokenService, Depends(get_token_service)],
    redis_client: Annotated[redis.Redis, Depends(get_redis_client)]
) -> AuthService:
    return AuthService(user_repo, token_service, user_profile_repo, redis_client)


# Dependency để lấy UserService
def get_user_service(
    user_repo: Annotated[UserRepository, Depends(get_user_repository)]
) -> UserService:
    return UserService(user_repo=user_repo)


# Dependency để lấy CategoryService
def get_category_service() -> CategoryService:
    category_repo = get_category_repository()
    return CategoryService(category_repo=category_repo)


def get_author_service() -> AuthorService:
    author_repo = get_author_repository()
    return AuthorService(author_repo=author_repo)


def get_book_service() -> BookService:
    book_repo = get_book_repository()
    category_repo = get_category_repository()
    author_repo = get_author_repository()
    return BookService(book_repo=book_repo, category_repo=category_repo, author_repo=author_repo)


def get_post_service() -> PostService:
    post_repo = get_post_repository()
    return PostService(post_repo=post_repo)

def get_notification_service() -> NotificationService:
    return NotificationService()

def get_upload_service() -> UploadService:
    user_profile_repo = get_user_profile_repository()
    return UploadService(user_profile_repo)

def get_media_services() -> MediaService:
    upload_service = get_upload_service()
    media_repo = get_media_repository()
    return MediaService(upload_service, media_repo=media_repo)

def get_user_profile_service() -> UserProfileService:
    user_profile_repo = get_user_profile_repository()
    return UserProfileService(user_profile_repo)