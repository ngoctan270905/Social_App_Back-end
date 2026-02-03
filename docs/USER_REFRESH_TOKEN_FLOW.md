Luồng Làm Mới Access Token (Refresh Token):

Đây là luồng xử lý khi Access Token cũ của người dùng hết hạn và client cần lấy một token mới mà không bắt người dùng đăng nhập lại.

1.  Client gửi yêu cầu làm mới token:
    Khi Access Token hết hạn, client tự động gửi một HTTP POST request đến API endpoint /api/v1/auth/refresh.
    Client không gửi dữ liệu trong body, thay vào đó, refresh_token (được lưu trong HttpOnly cookie từ lúc đăng nhập) sẽ tự động được đính kèm vào request.

2.  API Server xác thực Refresh Token:
    API Server nhận request và đọc refresh_token từ cookie.
    Server kiểm tra token này trong cơ sở dữ liệu để đảm bảo nó tồn tại và hợp lệ. Nếu không, request sẽ bị từ chối (yêu cầu người dùng đăng nhập lại).

3.  API Server thực hiện "Xoay Vòng Token" (Token Rotation):
    Nếu refresh_token hợp lệ, API Server ngay lập tức thu hồi (xóa) token đó khỏi cơ sở dữ liệu. Điều này đảm bảo mỗi refresh token chỉ được sử dụng một lần duy nhất, tăng cường bảo mật.

4.  API Server tạo và cấp phát bộ tokens mới:
    API Server tạo ra một Access Token hoàn toàn mới và một Refresh Token cũng hoàn toàn mới.
    Refresh Token mới này được lưu vào cơ sở dữ liệu để sử dụng cho lần làm mới tiếp theo.

5.  API Server trả bộ tokens mới về cho Client:
    API Server trả về response:
    Access Token mới được gửi trong body JSON.
    Refresh Token mới được gửi về dưới dạng một HttpOnly cookie mới, ghi đè lên cookie cũ.
