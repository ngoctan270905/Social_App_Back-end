Luồng Lấy Thông Tin Người Dùng (API /me):

Đây là luồng xử lý khi client muốn lấy thông tin của người dùng đang đăng nhập.

1.  Client gửi yêu cầu lấy thông tin:
    Client gửi một HTTP GET request đến API endpoint /api/v1/auth/me.
    Request này phải đính kèm Access Token còn hiệu lực trong Authorization header (ví dụ: Authorization: Bearer <your_access_token>).

2.  API Server xác thực Access Token:
    API Server nhận request và trích xuất Access Token từ header.
    Server thực hiện một loạt các bước xác thực: kiểm tra chữ ký, kiểm tra thời gian hết hạn của token.
    Quan trọng nhất, server kiểm tra xem token này có nằm trong "danh sách đen" (blacklist) trên Redis hay không. Một token sẽ bị đưa vào blacklist khi người dùng đăng xuất. Nếu token có trong blacklist, request sẽ bị từ chối.

3.  API Server truy vấn thông tin người dùng:
    Nếu Access Token hợp lệ, API Server sẽ lấy user_id từ nội dung của token.
    Server sử dụng user_id này để truy vấn cơ sở dữ liệu (MongoDB) và lấy ra thông tin chi tiết của người dùng (id, email, tên, ngày sinh...).

4.  API Server trả về thông tin người dùng:
    API Server trả về một response thành công, trong đó body JSON chứa thông tin chi tiết của người dùng (tất nhiên là không bao gồm mật khẩu hay các dữ liệu nhạy cảm khác).
