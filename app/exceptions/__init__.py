from fastapi import FastAPI

from app.exceptions.base import AppException
from app.exceptions.handlers import (
    rate_limit_exception_handler,
    http_exception_handler,
    generic_exception_handler, app_exception_handler
)
from fastapi.exceptions import HTTPException as StarletteHTTPException
from slowapi.errors import RateLimitExceeded


def add_exception_handlers(app: FastAPI):
    """
    Đăng ký tất cả các exception handlers vào ứng dụng FastAPI.
    """
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RateLimitExceeded, rate_limit_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)