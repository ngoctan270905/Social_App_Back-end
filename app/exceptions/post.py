from .base import AppException

class NotFoundError(AppException):
    status_code = 404
    message = "Không tìm thấy tài nguyên"

class ForbiddenError(AppException):
    status_code = 403
    message = "Bạn ko có quyền"
