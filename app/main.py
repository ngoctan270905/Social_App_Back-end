import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import JSONResponse
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

app.state.limiter = limiter


app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
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



# Configuration
cloudinary.config(
    cloud_name = settings.CLOUDINARY_CLOUD_NAME,
    api_key = settings.CLOUDINARY_API_KEY,
    api_secret = settings.CLOUDINARY_API_SECRET,
    secure=True
)

# Upload an image
# upload_result = cloudinary.uploader.upload("https://res.cloudinary.com/demo/image/upload/getting-started/shoes.jpg",
#                                            public_id="shoes")
# print(upload_result["secure_url"])
#
# # Optimize delivery by resizing and applying auto-format and auto-quality
# optimize_url, _ = cloudinary_url("shoes", fetch_format="auto", quality="auto")
# print(optimize_url)
#
# # Transform the image: auto-crop to square aspect_ratio
# auto_crop_url, _ = cloudinary_url("shoes", width=500, height=500, crop="auto", gravity="auto")
# print(auto_crop_url)