from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, news, uploads, profiles, conversations, comments
from app.api.v1.endpoints import notifications

api_router = APIRouter()

# api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])

api_router.include_router(
    comments.router,
    prefix="/comments",
    tags=["Comments"]
)

api_router.include_router(
    conversations.router,
    prefix="/conversations",
    tags=["Conversations"]
)

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

# ===== Auth routes =====
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Auth"]
)

# # ===== Users routes (Admin only) =====
# api_router.include_router(
#     users.router,
#     prefix="/users",
#     tags=["Users"]
# )

