"""
BƯỚC 3: HỆ THỐNG GIÁM SÁT THỜI GIAN THỰC (Nhận dạng Khuôn mặt & Cảnh Báo)
Phần mềm này sẽ hoạt động 24/7. Thỉnh thoảng nếu có người mới thêm vào từ Web,
nó tự động đọc file não bộ (.pkl) mới mà không cần đứng máy.
"""

import cv2
import numpy as np
import time
import os
import threading
import queue
import pickle
from PIL import Image
import customtkinter as ctk

from ultralytics import YOLO
from insightface.app import FaceAnalysis

import db_handler
from telegram_alert import send_telegram_photo

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

MODELS_DIR = "models"
EMBEDDINGS_FILE = os.path.join(MODELS_DIR, "embeddings.pkl")

SIMILARITY_THRESHOLD = 0.45
MOTION_AREA_THRESHOLD = 3000
ALERT_COOLDOWN_SEC = 20
DB_LOG_COOLDOWN_SEC = 30

def remove_accents(input_str):
    s1 = u'ÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝàáâãèéêìíòóôõùúýĂăĐđĨĩŨũƠơƯưẠạẢảẤấẦầẨẩẪẫẬậẮắẰằẲẳẴẵẶặẸẹẺẻẼẽẾếỀềỂểỄễỆệỈỉỊịỌọỎỏỐốỒồỔổỖỗỘộỚớỜờỞởỠỡỢợỤụỦủỨứỪừỬửỮữỰựỲỳỴỵỶỷỸỹ'
    s0 = u'AAAAEEEIIOOOOUUYaaaaeeeiioooouuyAaDdIiUuOoUuAaAaAaAaAaAaAaAaAaAaAaAaEeEeEeEeEeEeEeEeIiIiOoOoOoOoOoOoOoOoOoOoOoOoUuUuUuUuUuUuUuYyYyYyYy'
    s = ""
    for c in input_str:
        if c in s1: s += s0[s1.index(c)]
        else: s += c
    return s

class VideoCaptureThread(threading.Thread):
    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self.running = True
        
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=50, detectShadows=True)
        self.yolo_model = YOLO("yolov8n.pt")
        self.app_face = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
        self.app_face.prepare(ctx_id=0, det_size=(640, 640))
        
        self.known_faces = {}
        self.last_pkl_mtime = 0
        self.load_brain_from_pkl()
        
        self.last_alert_time = 0
        self.last_log_times = {} 
        
    def load_brain_from_pkl(self):
        """Đọc file não bộ thay vì đọc từng ảnh, giúp load siêu nhanh."""
        if not os.path.exists(EMBEDDINGS_FILE):
            print("[CẢNH BÁO] Chưa tìm thấy file Não Bộ embeddings.pkl! Hãy chạy Bước 2 trước.")
            return

        current_mtime = os.path.getmtime(EMBEDDINGS_FILE)
        if current_mtime > self.last_pkl_mtime:
            try:
                with open(EMBEDDINGS_FILE, 'rb') as f:
                    self.known_faces = pickle.load(f)
                self.last_pkl_mtime = current_mtime
                print(f"[AI RELOAD] Đã nạp lại {len(self.known_faces)} mạng Nơ-ron não bộ thành công!")
            except Exception as e:
                print(f"[LỖI ĐỌC PKL] Không thể đọc file: {e}")
        
    def run(self):
        cap = cv2.VideoCapture(0)
        db_handler.init_database_if_not_exists()
        
        last_brain_check_time = time.time()

        while self.running:
            # Hot-Reload File Pickle mỗi 10 Giây
            if time.time() - last_brain_check_time > 10:
                self.load_brain_from_pkl()
                last_brain_check_time = time.time()

            ret, frame = cap.read()
            if not ret:
                continue

            # Nén/Xử lý Motion
            fg_mask = self.bg_subtractor.apply(frame)
            _, fg_mask = cv2.threshold(fg_mask, 200, 255, cv2.THRESH_BINARY)
            motion_area = cv2.countNonZero(fg_mask)
            
            if motion_area > MOTION_AREA_THRESHOLD:
                # YOLO tracking Person
                results = self.yolo_model(frame, classes=[0], stream=True, verbose=False)
                person_detected = any(len(r.boxes) > 0 for r in results)
                
                if person_detected:
                    # InsightFace trích Vector nóng
                    faces = self.app_face.get(frame)
                    for face in faces:
                        best_match = "UNKNOWN"
                        best_sim = 0.0
                        face_emb = face.embedding
                        x1, y1, x2, y2 = face.bbox.astype(int)
                        
                        # So sánh 1 vs N list Trí Nhớ trong RAM (Lấy từ PKL)
                        for ma_sv, known_emb in self.known_faces.items():
                            sim = np.dot(face_emb, known_emb) / (np.linalg.norm(face_emb) * np.linalg.norm(known_emb))
                            if sim > best_sim and sim > SIMILARITY_THRESHOLD:
                                best_sim = sim
                                best_match = ma_sv
                                
                        # Mapping Tên
                        ho_ten_vn = db_handler.get_student_info(best_match)
                        ho_ten_khong_dau = remove_accents(ho_ten_vn)
                        color = (0, 255, 0) if best_match != "UNKNOWN" else (0, 0, 255)
                        
                        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                        display_text = "Ke La (Canh Bao)" if best_match == "UNKNOWN" else ho_ten_khong_dau
                        cv2.putText(frame, display_text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                        
                        current_time = time.time()
                        
                        # Database Logging
                        last_time = self.last_log_times.get(best_match, 0)
                        if current_time - last_time > DB_LOG_COOLDOWN_SEC:
                            sql_status = "Cảnh Báo" if best_match == "UNKNOWN" else "Hợp Lệ"
                            db_handler.log_attendance(best_match, sql_status)
                            
                            self.main_app.log_queue.put(f"{ho_ten_vn} ({sql_status})")
                            self.last_log_times[best_match] = current_time
                            
                            # Telegram Alert
                            if best_match == "UNKNOWN" and (current_time - self.last_alert_time > ALERT_COOLDOWN_SEC):
                                self.main_app.log_queue.put("🚨 GỬI TELEGRAM...")
                                send_telegram_photo(frame, "🚨 CẢNH BÁO: Phát hiện Kẻ Lạ!")
                                self.last_alert_time = current_time

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.main_app.latest_image = Image.fromarray(frame_rgb)

        cap.release()

    def stop(self):
        self.running = False


class FaceApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Hệ Thống Nhận Diện AI (Client) - Đồ Án Tốt Nghiệp")
        self.geometry("1100x700")

        self.latest_image = None
        self.log_queue = queue.Queue()

        self.grid_columnconfigure(0, weight=7)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(0, weight=1)

        self.video_frame = ctk.CTkFrame(self, corner_radius=10)
        self.video_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.video_frame.pack_propagate(False)
        
        self.camera_label = ctk.CTkLabel(self.video_frame, text="Đang khởi tạo Camera và Đọc Não Bộ AI...")
        self.camera_label.pack(expand=True, fill="both", padx=5, pady=5)

        self.sidebar = ctk.CTkFrame(self, corner_radius=10, fg_color="#1E1E1E", width=350)
        self.sidebar.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.sidebar.pack_propagate(False)
        
        self.title_lbl = ctk.CTkLabel(self.sidebar, text="DASHBOARD AN NINH", font=ctk.CTkFont(size=20, weight="bold"))
        self.title_lbl.pack(pady=(20, 10))
        
        self.sys_status = ctk.CTkLabel(self.sidebar, text="Trạng thái: AI Live ✅", text_color="#00FF00")
        self.sys_status.pack(pady=5)
        
        self.log_textbox = ctk.CTkTextbox(self.sidebar, font=ctk.CTkFont(size=14), wrap="word")
        self.log_textbox.pack(padx=15, pady=10, fill="both", expand=True)
        self.log_textbox.insert("0.0", "--- Lịch sử Quét mặt ---\n")
        self.log_textbox.configure(state="disabled")

        self.video_thread = VideoCaptureThread(self)
        self.video_thread.start()
        self.update_gui_loop()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def update_gui_loop(self):
        if self.latest_image is not None:
            w, h = self.video_frame.winfo_width(), self.video_frame.winfo_height()
            if w > 100 and h > 100:
                # Giữ nguyên tỉ lệ khung hình (aspect ratio) để không bị bóp méo
                frame_w, frame_h = w - 20, h - 20
                img_w, img_h = self.latest_image.size
                scale = min(frame_w / img_w, frame_h / img_h)
                new_w = int(img_w * scale)
                new_h = int(img_h * scale)
                img_resized = self.latest_image.resize((new_w, new_h), Image.LANCZOS)
                imgtk = ctk.CTkImage(light_image=img_resized, dark_image=img_resized, size=(new_w, new_h))
                self.camera_label.configure(image=imgtk, text="")
        
        while not self.log_queue.empty():
            text = self.log_queue.get()
            now_str = time.strftime("%H:%M:%S")
            self.log_textbox.configure(state="normal")
            self.log_textbox.insert("end", f"[{now_str}] {text}\n")
            self.log_textbox.see("end")
            self.log_textbox.configure(state="disabled")

        self.after(30, self.update_gui_loop)

    def on_closing(self):
        print("[INFO] Bắt đầu dọn dẹp bộ nhớ và tắt ứng dụng...")
        self.video_thread.stop()
        self.video_thread.join(timeout=2)
        self.destroy()

if __name__ == "__main__":
    app = FaceApp()
    app.mainloop()
