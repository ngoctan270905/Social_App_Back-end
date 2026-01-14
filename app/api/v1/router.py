from fastapi import APIRouter
from app.api.v1.endpoints import books, categories, authors, auth, users, news, uploads, profiles
from app.api.v1.endpoints import notifications

api_router = APIRouter()

api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])

api_router.include_router(
    news.router,
    prefix="/posts",
    tags=["Posts"]
)

api_router.include_router(
    profiles.router,
    prefix="/profiles",
    tags=["Profiles"]
)

api_router.include_router(
    uploads.router,
    prefix="/uploads",
    tags=["Uploads"]
)

# ===== Auth routes =====
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Auth"]
)

# ===== Users routes (Admin only) =====
api_router.include_router(
    users.router,
    prefix="/users",
    tags=["Users"]
)

# ===== Books routes =====
api_router.include_router(
    books.router,
    prefix="/books",
    tags=["Books"]
)

# ===== Categories routes =====
api_router.include_router(
    categories.router,
    prefix="/categories",
    tags=["Categories"]
)

# ===== Authors routes =====
api_router.include_router(
    authors.router,
    prefix="/authors",
    tags=["Authors"]
)
