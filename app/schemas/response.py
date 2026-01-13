from typing import Generic, TypeVar, Optional, Any
from pydantic.generics import GenericModel
from pydantic import BaseModel, Field

T = TypeVar('T')

# schema cho phản hồi thành công
class ResponseModel(GenericModel, Generic[T]):
    status: str = Field("success", description="Trạng thái của request")
    message: Optional[str] = Field(None, description="Thông điệp tùy chọn")
    data: Optional[T] = Field(None, description="Dữ liệu chính")

# schema cho lỗi
class ErrorResponse(BaseModel):
    status: str = Field("error", description="Trạng thái của request")
    message: str = Field(..., description="Mô tả lỗi chính")
    detail: Optional[Any] = Field(None, description="Chi tiết lỗi")