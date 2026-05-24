import os
import firebase_admin
from firebase_admin import credentials, messaging
from config import Config
from db.connection import execute_one

# Khởi tạo Firebase Admin
def init_firebase():
    key_path = os.path.join(Config.BASE_DIR, 'serviceAccountKey.json')
    if os.path.exists(key_path):
        if not firebase_admin._apps:
            cred = credentials.Certificate(key_path)
            firebase_admin.initialize_app(cred)
            print("[FCM] Đã khởi tạo Firebase Admin SDK thành công.")
    else:
        print("[FCM] CẢNH BÁO: Không tìm thấy file serviceAccountKey.json, Push Notification sẽ bị vô hiệu hóa.")

def send_push_notification(fcm_token, title, body, data=None):
    """Gửi thông báo đẩy tới 1 thiết bị"""
    if not firebase_admin._apps or not fcm_token:
        return False
        
    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
                image=data.get('image_url') if data else None
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

def notify_student_attendance(mssv, time_str, camera_name, image_url=None):
    """Lấy fcm_token của sinh viên và gửi thông báo"""
    sv = execute_one("SELECT fcm_token FROM sinh_vien WHERE mssv = %s", (mssv,))
    if sv and sv.get('fcm_token'):
        title = "Điểm danh thành công"
        body = f"Hệ thống ghi nhận bạn đã điểm danh lúc {time_str} tại {camera_name}."
        data = {}
        if image_url:
            data['image_url'] = image_url
        send_push_notification(sv['fcm_token'], title, body, data)
