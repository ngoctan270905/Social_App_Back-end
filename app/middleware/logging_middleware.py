from loguru import logger
import time
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Gán iD cho mỗi request
        request_id = str(uuid.uuid4())
        
        #  thông tin request
        method = request.method
        path = request.url.path
        client_ip = request.client.host
        
        # Ghi log trước khi xử lý
        logger.info(f"Request ID: {request_id} | Bắt đầu: {method} {path} | IP: {client_ip}")
        
        # Bắt đầu đếm thời gian
        start_time = time.time()
        
        # Chuyển request đi xử lý
        response = await call_next(request)
        
        # Kết thúc đếm thời gian và tính toán
        process_time = (time.time() - start_time) * 1000  # ms
        
        # Ghi log sau khi xử lý xong
        status_code = response.status_code
        logger.info(f"Request ID: {request_id} | Kết thúc: {method} {path} | Status: {status_code} | Thời gian: {process_time:.2f}ms")
        
        return response
