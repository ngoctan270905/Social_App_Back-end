from datetime import datetime
from zoneinfo import ZoneInfo  # Python 3.9+

# Múi giờ mặc định của project: Việt Nam
VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")

def now_vn() -> datetime:
    """
    Trả về thời gian hiện tại ở Việt Nam (timezone-aware)
    """
    return datetime.now(tz=VN_TZ)
