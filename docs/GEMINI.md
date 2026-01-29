🚫 NHÓM PHẢI TRÁNH 

❌ 1️⃣ Sequential I/O trong loop

Tránh await I/O trong vòng lặp

👉 Đây là bottleneck số 1, rất dễ gây lag toàn server khi scale (fan-out, broadcast, notify).

❌ 2️⃣ Blocking trong async

Tuyệt đối không block event loop

❌ CẤM:

time.sleep

gọi thư viện sync nặng

query DB sync trong async route

CPU-bound chạy trực tiếp trong event loop

👉 1 chỗ block → toàn bộ async server lag, không chỉ request đó.

❌ 3️⃣ Fan-out không kiểm soát

Không bắn 1 event cho N user mà không giới hạn

❌ CẤM:

broadcast trực tiếp cho hàng trăm / hàng nghìn user

không có limit song song

không timeout / retry

👉 Rất dễ tự DDoS chính server của mình, dù không ai tấn công.

❌ 4️⃣ Single Point of Failure

Không để 1 điểm chết kéo sập cả hệ thống

❌ Ví dụ cần tránh:

1 Redis instance không fallback

1 DB connection / pool quá nhỏ

1 global lock cho hot path

👉 Chết là chết cả cụm, không chỉ 1 feature.

⚠️ NHÓM KHÔNG CẤM – NHƯNG PHẢI KIỂM SOÁT
⚠️ 5️⃣ Bottleneck

Không tránh được, nhưng phải biết nó ở đâu

Yêu cầu:

xác định hot path

đo được (log / metric)

biết giới hạn hiện tại

👉 Bottleneck nguy hiểm nhất là bottleneck không ai biết.

⚠️ 6️⃣ Fan-out / Broadcast

Được làm, nhưng phải nghĩ tới scale

Cho phép khi:

group nhỏ

có giới hạn song song

có timeout / backpressure

Không assume “sẽ không nhiều user”.

⚠️ 7️⃣ Technical Debt

Được nợ, nhưng phải biết mình đang nợ

Cho phép:

MVP

deadline gấp

❌ Không cho phép:

nợ mà không ghi chú

nợ mà coi như feature hoàn chỉnh

👉 Technical debt không ghi lại = bug tương lai.

✅ NHÓM KHÔNG TRÁNH – NHƯNG PHẢI DÙNG ĐÚNG
✅ 8️⃣ Sequential (logic)

Sequential không xấu – sequential I/O mới xấu

Sequential bắt buộc trong:

validate

transaction

workflow có thứ tự

👉 Chỉ tránh sequential I/O, không phải tránh mọi sequential.

✅ 9️⃣ Latency / Throughput

Không tránh – phải đo – phải trade-off

latency thấp ≠ throughput cao

phải biết ưu tiên cái nào cho từng feature

✅ 🔟 Scaling (Horizontal / Vertical)

Scale đúng lúc – không scale mù

chưa hiểu bottleneck → đừng scale

scale là giải pháp sau, không phải đầu tiên

✅ 1️⃣1️⃣ Idempotent

Bắt buộc phải nghĩ tới

Đặc biệt khi có:

retry

webhook

pub/sub

distributed system

👉 Gửi lại không được tạo side-effect sai.

🧠 Tinh thần chung

“Code chạy được là chưa đủ.
Code phải chịu được fan-out, retry và scale.”