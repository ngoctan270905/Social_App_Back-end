import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import JSONResponse
from starlette.staticfiles import StaticFiles

from app.middleware.logging_middleware import LoggingMiddleware

from app.core.config import settings
from app.core.lifespan import lifespan
from app.core.rate_limiter import limiter
from app.core.logging import setup_logging

from app.exceptions import add_exception_handlers
from app.api.v1.router import api_router
from app.api.v1.endpoints.websockets import router as ws_router

# Khởi tạo cấu hình logging trước khi tạo app
setup_logging()

# Tạo instance FastAPI chính
app = FastAPI(title="Facebook-API", lifespan=lifespan)

app.mount(
    "/image",
    StaticFiles(directory="resource/image"),
    name="image"
)
app.mount(
    "/video",
    StaticFiles(directory="resource/video"),
    name="video"
)

# Danh sách domain frontend được phép gọi API
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "https://social-app-front-end-gamma.vercel.app",
    "http://localhost:8080"
]

# Thêm middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,      # Domain được phép truy cập
    allow_credentials=True,     # Cho phép gửi cookie
    allow_methods=["*"],        # Cho phép tất cả HTTP method
    allow_headers=["*"],        # Cho phép tất cả header
)

# Middleware quản lý session
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

# Middleware ghi log request/response
app.add_middleware(LoggingMiddleware)

# Đăng ký toàn bộ exception handler tùy chỉnh
add_exception_handlers(app)

# Đăng ký REST API với prefix /api/v1
app.include_router(api_router, prefix="/api/v1")

# Đăng ký WebSocket router
app.include_router(ws_router)


