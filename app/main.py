import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import JSONResponse
from starlette.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.core.config import settings
from app.middleware.logging_middleware import LoggingMiddleware
from app.core.lifespan import lifespan
from app.core.rate_limiter import limiter
from app.exceptions import add_exception_handlers
from app.api.v1.endpoints.websockets import router as ws_router
import cloudinary
import cloudinary.uploader
from cloudinary.utils import cloudinary_url
from app.core.logging import setup_logging

setup_logging()

app = FastAPI(title="Library API", lifespan=lifespan)

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

app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "https://social-app-front-end-gamma.vercel.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(LoggingMiddleware)

# đăng kí exception
add_exception_handlers(app)

app.include_router(api_router, prefix="/api/v1")
app.include_router(ws_router)

app.mount(
    "/image",
    StaticFiles(directory="resource/image"),
    name="image"
)


