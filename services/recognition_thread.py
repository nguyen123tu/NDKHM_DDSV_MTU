"""
Service: Background Thread Nhận Diện Khuôn Mặt Realtime.
Chạy trong thread riêng khi admin bấm "Bắt đầu điểm danh".
Gửi frame + kết quả qua SocketIO về frontend.
"""

import time
import base64
import threading
import os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from config import Config
from core.camera import get_camera_manager
from core.matcher import get_matcher
from services import attendance_service
from services import student_service


class RecognitionSession:
    """
    Phiên nhận diện khuôn mặt realtime.
    
    Quy trình:
    1. Kết nối camera qua CameraManager
    2. Load FaceMatcher (não bộ)
    3. Loop:
       a. Đọc frame → Motion detection
       b. Nếu có motion → InsightFace detect faces
       c. Với mỗi face: embed → match MSSV
       d. Nếu nhận ra → log attendance + emit SocketIO
       e. Nếu không nhận ra → emit alert
       f. Encode frame base64 → emit 'frame' event
    4. FPS giới hạn 15fps
    """

    def __init__(self, lop_id, camera_id, socketio):
        """
        Args:
            lop_id: ID lớp đang điểm danh
            camera_id: ID camera sử dụng
            socketio: Flask-SocketIO instance để emit events
        """
        self.lop_id = lop_id
        self.camera_id = camera_id
        self.socketio = socketio
        self._thread = None
        self._running = False
        self._lock = threading.Lock()

        # Background subtractor cho motion detection
        self._bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=500, varThreshold=50, detectShadows=True
        )
        
        # Tracking: cooldown thời gian emit cho từng MSSV (tránh spam)
        self._emit_cooldowns = {}  # {mssv: last_emit_timestamp}
        
        # Load font có hỗ trợ tiếng Việt cho PIL
        self._font = None
        try:
            # Dùng font Arial có sẵn trên Windows
            font_path = "C:/Windows/Fonts/arial.ttf"
            if os.path.exists(font_path):
                self._font = ImageFont.truetype(font_path, 20)
        except Exception:
            pass

    def _draw_vn_text(self, frame, text, position, color_bgr):
        """
        Vẽ text tiếng Việt lên frame bằng PIL (thay vì cv2.putText).
        
        Args:
            frame: numpy array BGR
            text: chuỗi Unicode cần vẽ
            position: (x, y) top-left
            color_bgr: tuple (B, G, R)
        Returns:
            numpy array BGR đã vẽ text
        """
        # Chuyển BGR → RGB cho PIL
        img_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img_pil)
        
        # Chuyển BGR → RGB cho color
        color_rgb = (color_bgr[2], color_bgr[1], color_bgr[0])
        
        x, y = position
        font = self._font or ImageFont.load_default()
        
        # Vẽ nền đen mờ sau text để dễ đọc
        bbox = draw.textbbox((x, y), text, font=font)
        padding = 4
        draw.rectangle(
            [bbox[0] - padding, bbox[1] - padding, bbox[2] + padding, bbox[3] + padding],
            fill=(0, 0, 0, 180)
        )
        
        # Vẽ text
        draw.text((x, y), text, font=font, fill=color_rgb)
        
        # Chuyển RGB → BGR cho OpenCV
        return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

    def start(self):
        """Khởi động thread nhận diện."""
        if self._running:
            return False

        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        print(f"[SESSION] Bắt đầu điểm danh lớp {self.lop_id}, camera {self.camera_id}")
        return True

    def stop(self):
        """Dừng thread nhận diện."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=3)
        print(f"[SESSION] Dừng điểm danh lớp {self.lop_id}")

    @property
    def is_running(self):
        return self._running

    def _run(self):
        """Main loop nhận diện (chạy trong thread riêng)."""
        from core.engine import get_engine

        # Khởi tạo AI Engine (InsightFace hoặc YOLOv8+ResNet50)
        engine = get_engine()
        detect_and_embed = engine['detect_and_embed']
        print(f"[SESSION] Sử dụng engine: {engine['name']}")

        # Kết nối camera
        cam_manager = get_camera_manager()
        if not cam_manager.is_connected(self.camera_id):
            cam_manager.connect(self.camera_id, self.camera_id)

        # Load matcher
        matcher = get_matcher()

        # Cooldown tracking
        last_brain_check = time.time()
        frame_interval = 1.0 / Config.MAX_FPS  # Giới hạn FPS

        while self._running:
            loop_start = time.time()

            # Hot-reload não bộ mỗi 10 giây
            if time.time() - last_brain_check > 10:
                matcher.reload_if_updated()
                last_brain_check = time.time()

            # Đọc frame
            frame = cam_manager.get_frame(self.camera_id)
            if frame is None:
                time.sleep(0.1)
                continue

            # Motion detection
            fg_mask = self._bg_subtractor.apply(frame)
            _, fg_mask = cv2.threshold(fg_mask, 200, 255, cv2.THRESH_BINARY)
            motion_area = cv2.countNonZero(fg_mask)

            names = []
            similarities = []
            bboxes = []

            if motion_area > Config.MOTION_AREA_THRESHOLD:
                # Phát hiện + trích xuất embedding (engine-agnostic)
                face_results = detect_and_embed(frame)

                for face in face_results:
                    embedding = face['embedding']
                    x1, y1, x2, y2 = face['bbox']

                    # So khớp
                    mssv, sim = matcher.match(embedding)
                    names.append(mssv)
                    similarities.append(sim)
                    bboxes.append([int(x1), int(y1), int(x2), int(y2)])

                    # Xử lý kết quả
                    if mssv != "UNKNOWN":
                        ho_ten = student_service.get_name_by_mssv(mssv)
                        
                        # Ghi vào DB (check-in hoặc check-out) — cooldown do service quản lý
                        log_result = attendance_service.log(
                            mssv=mssv,
                            lop_id=self.lop_id,
                            do_chinh_xac=sim,
                            camera_id=self.camera_id
                        )
                        
                        # Emit thông tin lên frontend (cooldown 60s tránh spam — đồng bộ với DB cooldown)
                        emit_key = mssv
                        now = time.time()
                        last_emit = self._emit_cooldowns.get(emit_key, 0)
                        
                        if now - last_emit > 60:  # Cooldown emit 60 giây
                            self._emit_cooldowns[emit_key] = now
                            
                            action = 'checkin'
                            if log_result and isinstance(log_result, dict):
                                action = log_result.get('action', 'checkin')
                            
                            self.socketio.emit('attendance_log', {
                                'mssv': mssv,
                                'ho_ten': ho_ten,
                                'similarity': round(sim, 2),
                                'thoi_gian': time.strftime("%H:%M:%S"),
                                'trang_thai': 'Co mat',
                                'action': action
                            })

                        # Vẽ box xanh
                        color = (0, 255, 0)
                        label = f"{ho_ten} ({sim:.0%})"
                    else:
                        # Kẻ lạ — vẽ box đỏ
                        color = (0, 0, 255)
                        label = "Ke La"

                        # Emit cảnh báo (cooldown 10s tránh spam)
                        now = time.time()
                        last_alert = self._emit_cooldowns.get('__alert__', 0)
                        if now - last_alert > 10:
                            self._emit_cooldowns['__alert__'] = now
                            self.socketio.emit('alert', {
                                'message': 'Phát hiện người lạ!',
                                'thoi_gian': time.strftime("%H:%M:%S")
                            })

                    # Vẽ bounding box lên frame
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    # Dùng PIL để vẽ text tiếng Việt (cv2.putText không hỗ trợ Unicode)
                    frame = self._draw_vn_text(frame, label, (x1, y1 - 28), color)

            # Encode frame thành base64 JPEG gửi về frontend
            # Resize để giảm bandwidth (max 640x480)
            h, w = frame.shape[:2]
            if w > 640:
                scale = 640 / w
                frame = cv2.resize(frame, (640, int(h * scale)))

            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
            frame_b64 = base64.b64encode(buffer).decode('utf-8')

            self.socketio.emit('frame', {
                'image': f'data:image/jpeg;base64,{frame_b64}',
                'bboxes': bboxes,
                'names': names,
                'similarities': [round(s, 2) for s in similarities]
            })

            # Giới hạn FPS
            elapsed = time.time() - loop_start
            if elapsed < frame_interval:
                time.sleep(frame_interval - elapsed)

        # Cleanup
        cam_manager.disconnect(self.camera_id)


# Global session tracker
_active_session = None


def get_active_session():
    """Lấy phiên điểm danh đang chạy (nếu có)."""
    global _active_session
    return _active_session


def start_session(lop_id, camera_id, socketio):
    """
    Bắt đầu phiên điểm danh mới.
    Nếu đang có phiên cũ → dừng trước.
    """
    global _active_session
    if _active_session and _active_session.is_running:
        _active_session.stop()

    _active_session = RecognitionSession(lop_id, camera_id, socketio)
    _active_session.start()
    return True


def stop_session():
    """Dừng phiên điểm danh hiện tại."""
    global _active_session
    if _active_session:
        _active_session.stop()
        _active_session = None
        return True
    return False
