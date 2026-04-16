"""
Core AI: Quản lý Camera (hỗ trợ multi-cam).
Thread-safe, hỗ trợ USB, IP, RTSP, RTMP.
"""

import cv2
import threading


class CameraManager:
    """
    Quản lý nhiều camera cùng lúc.
    
    Mỗi camera được lưu dưới dạng {camera_id: VideoCapture}.
    Thread-safe với threading.Lock cho mọi thao tác.
    """

    def __init__(self):
        self._cameras = {}           # {camera_id: cv2.VideoCapture}
        self._lock = threading.Lock()
        print("[CAMERA] CameraManager đã khởi tạo.")

    def connect(self, camera_id, source):
        """
        Kết nối tới camera.
        
        Args:
            camera_id: ID định danh camera (int hoặc string)
            source: Nguồn video:
                    - int (0, 1, 2...) → USB webcam
                    - string URL → IP/RTSP/RTMP camera
                    
        Returns:
            bool: True nếu kết nối thành công
        """
        with self._lock:
            # Ngắt camera cũ nếu có
            if camera_id in self._cameras:
                self._cameras[camera_id].release()

            # Cố gắng kết nối
            try:
                # Nếu source là chuỗi số "0", "1" thì chuyển thành int
                if isinstance(source, str) and source.isdigit():
                    source = int(source)

                cap = cv2.VideoCapture(source)
                if cap.isOpened():
                    self._cameras[camera_id] = cap
                    print(f"[CAMERA] Kết nối thành công camera {camera_id} (source={source})")
                    return True
                else:
                    print(f"[CAMERA] Không thể kết nối camera {camera_id} (source={source})")
                    return False
            except Exception as e:
                print(f"[CAMERA LỖI] {e}")
                return False

    def disconnect(self, camera_id):
        """Ngắt kết nối camera."""
        with self._lock:
            if camera_id in self._cameras:
                self._cameras[camera_id].release()
                del self._cameras[camera_id]
                print(f"[CAMERA] Đã ngắt camera {camera_id}")
                return True
            return False

    def disconnect_all(self):
        """Ngắt tất cả camera."""
        with self._lock:
            for cam_id, cap in self._cameras.items():
                cap.release()
            self._cameras.clear()
            print("[CAMERA] Đã ngắt tất cả camera.")

    def get_frame(self, camera_id):
        """
        Đọc 1 frame từ camera.
        
        Args:
            camera_id: ID camera
            
        Returns:
            numpy array: Frame BGR, hoặc None nếu lỗi
        """
        with self._lock:
            cap = self._cameras.get(camera_id)
            if cap is None or not cap.isOpened():
                return None
            ret, frame = cap.read()
            if not ret:
                return None
            return frame

    def is_connected(self, camera_id):
        """Kiểm tra camera có đang kết nối không."""
        with self._lock:
            cap = self._cameras.get(camera_id)
            return cap is not None and cap.isOpened()

    def list_connected(self):
        """Danh sách camera đang kết nối."""
        with self._lock:
            return list(self._cameras.keys())

    @staticmethod
    def list_available_usb(max_test=10):
        """
        Quét tìm camera USB có sẵn trên máy tính.
        
        Args:
            max_test: Số index tối đa để thử (0 → max_test-1)
            
        Returns:
            list[int]: Danh sách index camera USB hoạt động
        """
        available = []
        for i in range(max_test):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                available.append(i)
                cap.release()
        return available


# Singleton instance
_instance = None


def get_camera_manager():
    """Lấy singleton instance của CameraManager."""
    global _instance
    if _instance is None:
        _instance = CameraManager()
    return _instance


if __name__ == '__main__':
    # Test: Quét USB camera và hiển thị feed
    print("=== TEST CAMERA MANAGER ===")
    available = CameraManager.list_available_usb()
    print(f"Camera USB có sẵn: {available}")

    if available:
        manager = get_camera_manager()
        cam_id = available[0]
        manager.connect(cam_id, cam_id)

        while True:
            frame = manager.get_frame(cam_id)
            if frame is None:
                break
            cv2.imshow(f"Camera {cam_id}", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        manager.disconnect_all()
        cv2.destroyAllWindows()
