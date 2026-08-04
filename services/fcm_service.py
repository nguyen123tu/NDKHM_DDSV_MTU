import os
import firebase_admin
from firebase_admin import credentials, messaging
from config import Config
from db.connection import execute_one


# Khởi tạo Firebase Admin
def init_firebase():
    key_path = os.path.join(Config.BASE_DIR, "serviceAccountKey.json")
    if os.path.exists(key_path):
        if not firebase_admin._apps:
            cred = credentials.Certificate(key_path)
            firebase_admin.initialize_app(cred)
            print("[FCM] Đã khởi tạo Firebase Admin SDK thành công.")
    else:
        print(
            "[FCM] CẢNH BÁO: Không tìm thấy file serviceAccountKey.json, Push Notification sẽ bị vô hiệu hóa."
        )


def send_push_notification(fcm_token, title, body, data=None):
    """Gửi thông báo đẩy tới 1 thiết bị"""
    if not firebase_admin._apps or not fcm_token:
        return False

    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title, body=body, image=data.get("image_url") if data else None
            ),
            data=data or {},
            token=fcm_token,
        )
        response = messaging.send(message)
        print(f"[FCM] Gửi thông báo thành công: {response}")
        return True
    except Exception as e:
        print(f"[FCM] Lỗi gửi thông báo: {e}")
        return False


def notify_student_attendance(
    mssv, time_str, camera_name, image_url=None, trang_thai="Co mat", di_tre_phut=0
):
    """Lấy fcm_token của sinh viên và gửi thông báo"""
    sv = execute_one("SELECT fcm_token FROM sinh_vien WHERE mssv = %s", (mssv,))
    if sv and sv.get("fcm_token"):
        if trang_thai == "Tre":
            title = "Cảnh báo đi trễ!"
            body = f"Hệ thống ghi nhận bạn đã điểm danh lúc {time_str} tại {camera_name}. Bạn đã đi trễ {di_tre_phut} phút."
        else:
            title = "Điểm danh thành công"
            body = f"Hệ thống ghi nhận bạn đã điểm danh đúng giờ lúc {time_str} tại {camera_name}."

        data = {}
        if image_url:
            data["image_url"] = image_url
        send_push_notification(sv["fcm_token"], title, body, data)


def send_custom_notification(title, body, mssv_list=None):
    """Gửi thông báo tuỳ chỉnh cho danh sách MSSV (hoặc tất cả nếu mssv_list trống)"""
    from db.connection import execute_query

    if mssv_list and len(mssv_list) > 0:
        # Nếu có danh sách mssv cụ thể
        format_strings = ",".join(["%s"] * len(mssv_list))
        sql = f"SELECT fcm_token FROM sinh_vien WHERE mssv IN ({format_strings}) AND fcm_token IS NOT NULL"
        users = execute_query(sql, tuple(mssv_list))
    else:
        # Nếu gửi cho tất cả
        sql = "SELECT fcm_token FROM sinh_vien WHERE fcm_token IS NOT NULL"
        users = execute_query(sql)

    tokens = [u["fcm_token"] for u in users if u.get("fcm_token")]

    if not tokens:
        print("[FCM] Không có token nào để gửi thông báo.")
        return 0

    success_count = 0
    # Gửi qua vòng lặp (vì số lượng có thể ít, nếu nhiều nên dùng messaging.send_each_for_multicast)
    # Tuy nhiên với số lượng nhỏ sinh viên, send_each_for_multicast là tối ưu
    if firebase_admin._apps:
        try:
            # Chia nhỏ thành các batch 500 token (giới hạn của Firebase)
            batch_size = 500
            for i in range(0, len(tokens), batch_size):
                batch_tokens = tokens[i : i + batch_size]
                message = messaging.MulticastMessage(
                    notification=messaging.Notification(title=title, body=body),
                    tokens=batch_tokens,
                )
                response = messaging.send_each_for_multicast(message)
                success_count += response.success_count
            print(
                f"[FCM] Đã gửi thông báo multicast thành công tới {success_count}/{len(tokens)} thiết bị."
            )
        except Exception as e:
            print(f"[FCM] Lỗi gửi thông báo multicast: {e}")

    return success_count
