from .base import AppException

class EmailAlreadyExistsError(AppException):
    status_code = 400
    message = "Email này đã được sử dụng!"

class UserNotFoundError(AppException):
    status_code = 404
    message = "User không tồn tại"

class RefreshTokenNotFoundError(AppException):
    status_code = 404
    message = "User không tồn tại"

class XacMinhError(AppException):
    status_code = 400
    message = "Email này đã được xác minh"

class OTPKhongTonTai(AppException):
    status_code = 400
    message = "Mã OTP đã hết hạn hoặc không tồn tại"

class OTPKhongChinhXac(AppException):
    status_code = 400
    message = "Mã OTP không đúng. Vui lòng thử lại"

class XacMinhEmail(AppException):
    status_code = 401
    message = "Vui lòng xác minh email"

class Ban(AppException):
    status_code = 403
    message = "Tài khoản của bạn đã bị khóa :)))"

class UserNotFoundErrorMail(AppException):
    status_code = 404
    message = "Tài khoản hoặc mật khẩu không chính xác!"

class UserInvalidForToken(AppException):
    status_code = 401
    message = "Không tìm thấy người dùng với Refresh Token"






