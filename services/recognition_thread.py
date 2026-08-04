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

    def __init__(
        self,
        lop_id,
        camera_id,
        socketio,
        start_time="07:00",
        phien_id=None,
        scheduled_start=None,
        checkin_close_at=None,
    ):
        """
        Args:
            lop_id: ID lớp đang điểm danh
            camera_id: ID camera sử dụng
            socketio: Flask-SocketIO instance để emit events
            start_time: Giờ quy định bắt đầu tiết học (VD: "07:00")
            phien_id: ID phiên điểm danh trong CSDL
            scheduled_start: datetime giờ học dự kiến
            checkin_close_at: datetime giờ đóng check-in
        """
        self.lop_id = lop_id
        self.camera_id = camera_id
        self.socketio = socketio
        self.start_time = start_time
        self.phien_id = phien_id
        self.scheduled_start = scheduled_start
        self.checkin_close_at = checkin_close_at
        self._thread = None
        self._running = False
        self._camera_connected = True
        self._lock = threading.Lock()

        # Background subtractor cho motion detection
        self._bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=500, varThreshold=50, detectShadows=True
        )

        # Tracking: cooldown thời gian emit cho từng MSSV (tránh spam)
        self._emit_cooldowns = {}  # {mssv: last_emit_timestamp}

        # Tracking: SV đã điểm danh trong phiên này → không ghi lại
        self._attended_students = set()  # {'mssv1', 'mssv2', ...}

        # Tracking: số lần nhận diện liên tiếp để ổn định (tránh nhận diện nhầm ở frame đầu)
        self._match_history = {}  # {mssv: count}

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
            [
                bbox[0] - padding,
                bbox[1] - padding,
                bbox[2] + padding,
                bbox[3] + padding,
            ],
            fill=(0, 0, 0, 180),
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
        self._thread = self.socketio.start_background_task(target=self._run)
        print(f"[SESSION] Bắt đầu điểm danh lớp {self.lop_id}, camera {self.camera_id}")
        return True

    def stop(self):
        """Dừng thread nhận diện."""
        self._running = False
        if self._thread and hasattr(self._thread, "join"):
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
        detect_and_embed = engine["detect_and_embed"]
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
            bboxes, names, similarities = [], [], []

            # Hot-reload não bộ mỗi 10 giây
            if time.time() - last_brain_check > 10:
                matcher.reload_if_updated()
                last_brain_check = time.time()

            # Đọc frame — Camera lỗi không làm mất phiên
            frame = cam_manager.get_frame(self.camera_id)
            if frame is None:
                if self._camera_connected:
                    self._camera_connected = False
                    self.socketio.emit(
                        "camera_status",
                        {
                            "status": "CAMERA_DISCONNECTED",
                            "message": "Camera mất kết nối. Phiên vẫn tiếp tục trong DB. App vẫn có thể điểm danh.",
                            "camera_id": self.camera_id,
                        },
                    )
                    print(
                        f"[SESSION] ⚠️ Camera {self.camera_id} mất kết nối. Phiên {self.phien_id} vẫn mở."
                    )
                time.sleep(1)  # Thử lại sau 1 giây
                # Thử kết nối lại camera
                try:
                    cam_manager.connect(self.camera_id, self.camera_id)
                except Exception:
                    pass
                continue
            else:
                if not self._camera_connected:
                    self._camera_connected = True
                    self.socketio.emit(
                        "camera_status",
                        {
                            "status": "CAMERA_CONNECTED",
                            "message": "Camera đã kết nối lại.",
                            "camera_id": self.camera_id,
                        },
                    )
                    print(f"[SESSION] ✅ Camera {self.camera_id} đã kết nối lại.")

            # TỐI ƯU HIỆU NĂNG: Resize frame ngay từ đầu để giảm độ trễ của AI
            # Giảm kích thước ảnh xuống max width 640px trước khi đưa vào YOLO/InsightFace
            h, w = frame.shape[:2]
            if w > 640:
                scale = 640 / w
                frame = cv2.resize(frame, (640, int(h * scale)))

            # Motion detection
            fg_mask = self._bg_subtractor.apply(frame)
            _, fg_mask = cv2.threshold(fg_mask, 200, 255, cv2.THRESH_BINARY)
            motion_area = cv2.countNonZero(fg_mask)

            # Biến đếm frame để bỏ qua (frame skipping)
            if not hasattr(self, "_frame_count"):
                self._frame_count = 0
                self._last_ai_results = []
            self._frame_count += 1

            if motion_area > Config.MOTION_AREA_THRESHOLD:
                # TỐI ƯU HIỆU NĂNG: Với YOLO11 và MAX_FPS=30, có thể xử lý AI trên mỗi 2 frame (đạt ~15 FPS thực tế cho AI)
                if self._frame_count % 2 == 0:
                    face_results = detect_and_embed(frame)
                    self._last_ai_results = []

                    current_frame_mssvs = set()

                    for face in face_results:
                        embedding = face["embedding"]
                        x1, y1, x2, y2 = face["bbox"]

                        # So khớp
                        mssv, sim = matcher.match(embedding)
                        original_mssv = mssv
                        ho_ten = (
                            student_service.get_name_by_mssv(mssv)
                            if mssv != "UNKNOWN"
                            else "Người lạ"
                        )

                        if original_mssv != "UNKNOWN":
                            current_frame_mssvs.add(original_mssv)

                        # ─── Heuristic Liveness Check (Chống giả mạo) ───
                        is_spoof = False
                        spoof_reason = ""
                        face_roi = frame[
                            max(0, int(y1)) : int(y2), max(0, int(x1)) : int(x2)
                        ]
                        if face_roi.size > 0:
                            gray_roi = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
                            blur_score = cv2.Laplacian(gray_roi, cv2.CV_64F).var()

                            hsv_roi = cv2.cvtColor(face_roi, cv2.COLOR_BGR2HSV)
                            v_channel = hsv_roi[:, :, 2]
                            glare_ratio = np.sum(v_channel > 240) / (
                                v_channel.size + 1e-6
                            )

                            if (x2 - x1) < 90 or (y2 - y1) < 90:
                                is_spoof = True
                                spoof_reason = f"Khuôn mặt quá nhỏ, cần tiến lại gần"
                            elif blur_score < 10.0:
                                is_spoof = True
                                spoof_reason = f"Ảnh quá mờ ({blur_score:.1f})"
                            elif glare_ratio > 0.40:
                                is_spoof = True
                                spoof_reason = f"Phát sáng màn hình ({glare_ratio:.2%})"

                        # ─── DeepFace Anti-Spoofing: Lọc khuôn mặt giả ───
                        if (
                            face.get("is_real") is not None
                            and not face.get("is_real", True)
                        ) or is_spoof:
                            final_reason = (
                                spoof_reason
                                if is_spoof
                                else f"score={face.get('antispoof_score', 0):.2f}"
                            )

                            now = time.time()

                            # Log gian lận nếu nhận diện được sinh viên (Cooldown 10s cho mỗi MSSV)
                            log_key = f"db_spoof_{mssv}"
                            if mssv != "UNKNOWN" and (
                                now - self._emit_cooldowns.get(log_key, 0) > 10
                            ):
                                self._emit_cooldowns[log_key] = now
                                print(
                                    f"[SESSION] ⚠️ GHI LOG GIAN LẬN: {mssv} - {final_reason}"
                                )
                                from db.connection import execute_one, execute_update

                                sv_temp = execute_one(
                                    "SELECT id FROM sinh_vien WHERE mssv = %s", (mssv,)
                                )
                                if sv_temp:
                                    execute_update(
                                        "INSERT INTO gian_lan_log (sinh_vien_id, loai_gian_lan, chi_tiet) VALUES (%s, %s, %s)",
                                        (
                                            sv_temp["id"],
                                            "Spoofing",
                                            f"Phát hiện qua Live Camera: {final_reason}. Tỉ lệ: {sim:.2f}",
                                        ),
                                    )

                            self._last_ai_results.append(
                                {
                                    "mssv": mssv if mssv != "UNKNOWN" else "SPOOFED",
                                    "sim": sim,
                                    "ho_ten": ho_ten,
                                    "bbox": [int(x1), int(y1), int(x2), int(y2)],
                                    "is_spoofed": True,
                                }
                            )

                            # Cảnh báo spoofing qua SocketIO (Cooldown 5s cho UI alert)
                            last_spoof_alert = self._emit_cooldowns.get("__spoof__", 0)
                            if now - last_spoof_alert > 5:
                                self._emit_cooldowns["__spoof__"] = now
                                self.socketio.emit(
                                    "alert",
                                    {
                                        "message": f"⚠️ Phát hiện hình ảnh giả mạo! ({ho_ten})",
                                        "type": "spoofing",
                                        "thoi_gian": time.strftime("%H:%M:%S"),
                                    },
                                )
                            continue

                        # ─── Ổn định nhận diện (Temporal Smoothing) ───
                        # Chống nhận diện nhầm ở những frame đầu tiên khi camera mới mở hoặc người dùng mới bước vào
                        if original_mssv != "UNKNOWN":
                            self._match_history[original_mssv] = (
                                self._match_history.get(original_mssv, 0) + 1
                            )
                            # Cần ít nhất 4 frame liên tiếp nhận diện cùng 1 người (khoảng 0.5s) mới xác nhận
                            if self._match_history[original_mssv] < 4:
                                mssv = "UNKNOWN"
                                ho_ten = f"Đang xác thực ({self._match_history[original_mssv]}/4)..."
                                # Không lưu điểm danh nếu chưa xác thực xong

                        result_item = {
                            "mssv": mssv,
                            "sim": sim,
                            "ho_ten": ho_ten,
                            "bbox": [int(x1), int(y1), int(x2), int(y2)],
                        }

                        # ─── DeepFace Face Analysis: Phân tích thuộc tính ───
                        analysis_actions = getattr(
                            Config, "DEEPFACE_ANALYSIS_ACTIONS", ""
                        )
                        if analysis_actions and "analyze_face" in engine:
                            try:
                                actions_tuple = tuple(
                                    a.strip()
                                    for a in analysis_actions.split(",")
                                    if a.strip()
                                )
                                if actions_tuple and self._frame_count % 9 == 0:
                                    # Chỉ phân tích mỗi 9 frame (tiết kiệm CPU)
                                    face_crop = frame[
                                        max(0, int(y1)) : int(y2),
                                        max(0, int(x1)) : int(x2),
                                    ]
                                    if face_crop.size > 0:
                                        analysis_results = engine["analyze_face"](
                                            face_crop, actions=actions_tuple
                                        )
                                        if analysis_results:
                                            analysis = analysis_results[0]
                                            result_item["age"] = analysis.get("age")
                                            result_item["gender"] = analysis.get(
                                                "gender"
                                            )
                                            result_item["emotion"] = analysis.get(
                                                "dominant_emotion"
                                            )
                            except Exception as e:
                                pass  # Không crash nếu phân tích lỗi

                        self._last_ai_results.append(result_item)

                        # Xử lý kết quả & Điểm danh — dùng record_attendance()
                        if mssv != "UNKNOWN":
                            from db.connection import execute_one

                            sv_db = execute_one(
                                "SELECT id, lop_id FROM sinh_vien WHERE mssv = %s",
                                (mssv,),
                            )
                            if sv_db and str(sv_db.get("lop_id")) == str(self.lop_id):
                                face_crop = frame[
                                    max(0, int(y1)) : int(y2), max(0, int(x1)) : int(x2)
                                ]
                                log_result = attendance_service.record_attendance(
                                    session_id=self.phien_id,
                                    student_id=sv_db["id"],
                                    method="FACE_CAMERA",
                                    confidence=sim,
                                    camera_id=self.camera_id,
                                    face_image=(
                                        face_crop if face_crop.size > 0 else None
                                    ),
                                )
                            else:
                                # Cảnh báo sinh viên khác lớp
                                log_result = {
                                    "success": False,
                                    "action": "wrong_class",
                                    "error_code": "WRONG_CLASS",
                                }

                            # Emit thông tin lên frontend (cooldown 60s tránh spam)
                            emit_key = mssv
                            now = time.time()
                            last_emit = self._emit_cooldowns.get(emit_key, 0)

                            if now - last_emit > 10:
                                if (
                                    isinstance(log_result, dict)
                                    and log_result.get("success")
                                    or (
                                        isinstance(log_result, dict)
                                        and log_result.get("action") == "wrong_class"
                                        and now - last_emit > 60
                                    )
                                ):
                                    self._emit_cooldowns[emit_key] = now

                                    action = log_result.get("action", "checkin")
                                    status = log_result.get("status", "PRESENT")
                                    if status == "LATE":
                                        action = "late"

                                    avatar_path = student_service.get_avatar_path(mssv)

                                    self.socketio.emit(
                                        "attendance_log",
                                        {
                                            "mssv": mssv,
                                            "ho_ten": ho_ten,
                                            "similarity": round(sim, 2),
                                            "thoi_gian": time.strftime("%H:%M:%S"),
                                            "trang_thai": log_result.get(
                                                "display_status", "Có mặt"
                                            ),
                                            "status": status,
                                            "action": action,
                                            "avatar": avatar_path,
                                        },
                                    )
                        else:
                            # Cảnh báo người lạ (người chưa đăng ký) trên Dashboard
                            now = time.time()
                            last_unknown_alert = self._emit_cooldowns.get(
                                "__unknown__", 0
                            )

                            # Cảnh báo tối đa 1 lần mỗi 5 giây để tránh spam
                            if now - last_unknown_alert > 5:
                                self._emit_cooldowns["__unknown__"] = now
                                self.socketio.emit(
                                    "alert",
                                    {
                                        "message": "⚠️ Phát hiện Người lạ (chưa đăng ký)",
                                        "type": "warning",
                                        "thoi_gian": time.strftime("%H:%M:%S"),
                                    },
                                )

                    # Reset/Giảm số đếm cho những MSSV không có trong frame này
                    for m in list(self._match_history.keys()):
                        if m not in current_frame_mssvs:
                            self._match_history[m] = max(0, self._match_history[m] - 1)

                # Vẽ bounding box từ kết quả lưu trữ (kể cả những frame không quét AI)
                for res in self._last_ai_results:
                    x1, y1, x2, y2 = res["bbox"]
                    mssv = res["mssv"]

                    bboxes.append([x1, y1, x2, y2])
                    names.append(mssv)
                    similarities.append(res["sim"])

                    if res.get("is_spoofed"):
                        # Khuôn mặt giả mạo — Đỏ cảnh báo
                        color = (0, 0, 255)  # BGR for Red
                        label = "⚠ GIẢ MẠO"
                    elif mssv != "UNKNOWN":
                        color = (0, 255, 0)  # Lục
                        label = f"{res['ho_ten']} ({res['sim']:.0%})"
                        # Thêm thông tin phân tích nếu có
                        extra_info = []
                        if res.get("age"):
                            extra_info.append(f"{int(res['age'])}t")
                        if res.get("gender"):
                            extra_info.append(res["gender"])
                        if res.get("emotion"):
                            extra_info.append(res["emotion"])
                        if extra_info:
                            label += f" [{', '.join(extra_info)}]"
                    else:
                        color = (0, 165, 255)  # Cam cho lúc đang chờ/chưa rõ
                        label = "Đang phân tích..."

                    # Vẽ khung dạng góc (Bracket corners) thay vì hình chữ nhật kín
                    length = 30
                    thickness = 3
                    # Top-left
                    cv2.line(frame, (x1, y1), (x1 + length, y1), color, thickness)
                    cv2.line(frame, (x1, y1), (x1, y1 + length), color, thickness)
                    # Top-right
                    cv2.line(frame, (x2, y1), (x2 - length, y1), color, thickness)
                    cv2.line(frame, (x2, y1), (x2, y1 + length), color, thickness)
                    # Bottom-left
                    cv2.line(frame, (x1, y2), (x1 + length, y2), color, thickness)
                    cv2.line(frame, (x1, y2), (x1, y2 - length), color, thickness)
                    # Bottom-right
                    cv2.line(frame, (x2, y2), (x2 - length, y2), color, thickness)
                    cv2.line(frame, (x2, y2), (x2, y2 - length), color, thickness)

                    frame = self._draw_vn_text(frame, label, (x1, y1 - 28), color)
            else:
                self._last_ai_results = []  # Xóa box nếu không còn chuyển động

            # Encode frame thành base64 JPEG gửi về frontend
            _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
            frame_b64 = base64.b64encode(buffer).decode("utf-8")

            self.socketio.emit(
                "frame",
                {
                    "image": f"data:image/jpeg;base64,{frame_b64}",
                    "bboxes": bboxes,
                    "names": names,
                    "similarities": [round(s, 2) for s in similarities],
                },
            )

            # Giới hạn FPS
            elapsed = time.time() - loop_start
            if elapsed < frame_interval:
                self.socketio.sleep(frame_interval - elapsed)
            else:
                self.socketio.sleep(0)  # Đảm bảo luôn nhường CPU cho event loop

        # Cleanup
        cam_manager.disconnect(self.camera_id)


# Global session tracker
_active_session = None


def get_active_session():
    """Lấy phiên điểm danh đang chạy (nếu có)."""
    global _active_session
    return _active_session


def start_session(lop_id, camera_id, socketio, start_time="07:00", admin_id=None):
    """
    Bắt đầu phiên điểm danh mới.
    Tạo phiên trong DB → Web và App đều nhìn thấy cùng phiên.
    Nếu đang có phiên cũ → dừng trước.
    """
    global _active_session
    if _active_session and _active_session.is_running:
        stop_session(admin_id=admin_id)

    from services.attendance_session_service import AttendanceSessionService
    from datetime import datetime, date

    try:
        st_obj = datetime.strptime(start_time, "%H:%M").time()
        gio_du_kien = datetime.combine(date.today(), st_obj)
    except Exception:
        gio_du_kien = datetime.now()

    sess_row, err = AttendanceSessionService.create_session(
        lop_id=lop_id,
        admin_id=admin_id,
        loai_phien="WEB_CAMERA",
        gio_hoc_du_kien=gio_du_kien,
    )
    phien_id = sess_row["id"] if sess_row else None

    # Lấy metadata phiên để truyền cho recognition thread
    scheduled_start = gio_du_kien
    checkin_close_at = (
        sess_row.get("dong_checkin") or sess_row.get("het_han") if sess_row else None
    )

    _active_session = RecognitionSession(
        lop_id,
        camera_id,
        socketio,
        start_time,
        phien_id=phien_id,
        scheduled_start=scheduled_start,
        checkin_close_at=checkin_close_at,
    )
    _active_session.start()
    return phien_id  # Trả session_id để frontend có thể dùng


def stop_session(admin_id=None):
    """Dừng phiên điểm danh hiện tại và chốt kết quả."""
    global _active_session
    if _active_session:
        from services.attendance_session_service import AttendanceSessionService

        close_result = None
        if _active_session.phien_id:
            close_result = AttendanceSessionService.close_session(
                _active_session.phien_id, admin_id=admin_id
            )
        _active_session.stop()
        _active_session = None
        return close_result or True
    return False
