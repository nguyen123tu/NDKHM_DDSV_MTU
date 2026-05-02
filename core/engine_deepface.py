"""
Core AI: Engine DeepFace — Tích hợp thư viện DeepFace (serengil/deepface).

Hỗ trợ đa dạng model nhận diện khuôn mặt:
  - ArcFace, Facenet512, GhostFaceNet, VGG-Face, SFace, Dlib, ...
  
Hỗ trợ đa dạng detector:
  - retinaface, mtcnn, yolov8, mediapipe, opencv, centerface, ...
  
Tính năng bổ sung:
  - Anti-spoofing (chống giả mạo khuôn mặt)
  - Phân tích thuộc tính (tuổi, giới tính, cảm xúc, sắc tộc)
"""

import numpy as np
import cv2


def _get_deepface():
    """Lazy import DeepFace module."""
    from deepface import DeepFace
    return DeepFace


# ─── Mapping model → embedding dimension ────────────────────────────────
MODEL_DIMS = {
    'VGG-Face': 4096,
    'Facenet': 128,
    'Facenet512': 512,
    'OpenFace': 128,
    'DeepFace': 4096,
    'DeepID': 160,
    'Dlib': 128,
    'ArcFace': 512,
    'SFace': 128,
    'GhostFaceNet': 512,
    'Buffalo_L': 512,
}


def build_deepface_engine(model_name='ArcFace', detector_backend='retinaface',
                          anti_spoofing=False):
    """
    Xây dựng DeepFace engine tương thích với Factory pattern hiện tại.

    Args:
        model_name: Model nhận diện. Mặc định 'ArcFace'.
            Options: VGG-Face, Facenet, Facenet512, OpenFace, DeepFace,
                     DeepID, Dlib, ArcFace, SFace, GhostFaceNet, Buffalo_L
        detector_backend: Detector phát hiện khuôn mặt. Mặc định 'retinaface'.
            Options: opencv, retinaface, mtcnn, ssd, dlib, mediapipe,
                     yolov8n, yolov11n, centerface, yunet, skip
        anti_spoofing: Bật/tắt anti-spoofing (chống giả mạo). Mặc định False.

    Returns:
        dict: {
            'name': str,
            'embedding_dim': int,
            'detect_and_embed': callable,
            'analyze_face': callable,      # Phân tích thuộc tính khuôn mặt
            'verify_liveness': callable,   # Kiểm tra khuôn mặt thật/giả
        }
    """
    DeepFace = _get_deepface()

    print(f"[ENGINE] Đang khởi tạo DeepFace ({model_name} + {detector_backend})...")

    # Pre-build model để giảm latency lần đầu
    try:
        DeepFace.build_model(model_name=model_name, task='facial_recognition')
        print(f"[ENGINE] Model nhận diện '{model_name}' đã tải thành công.")
    except Exception as e:
        print(f"[ENGINE CẢNH BÁO] Không thể pre-load model '{model_name}': {e}")

    try:
        DeepFace.build_model(model_name=detector_backend, task='face_detector')
        print(f"[ENGINE] Detector '{detector_backend}' đã tải thành công.")
    except Exception as e:
        print(f"[ENGINE CẢNH BÁO] Không thể pre-load detector '{detector_backend}': {e}")

    embedding_dim = MODEL_DIMS.get(model_name, 512)
    print(f"[ENGINE] DeepFace đã sẵn sàng. "
          f"Model={model_name}, Detector={detector_backend}, "
          f"Dim={embedding_dim}, Anti-Spoof={'ON' if anti_spoofing else 'OFF'}")

    def detect_and_embed(frame):
        """
        DeepFace detect + embed.

        Args:
            frame: numpy array BGR từ OpenCV

        Returns:
            list[dict]: [{
                'bbox': [x1, y1, x2, y2],
                'embedding': numpy array,
                'confidence': float,
                'is_real': bool (nếu anti_spoofing=True),
                'antispoof_score': float (nếu anti_spoofing=True),
            }, ...]
        """
        if frame is None or frame.size == 0:
            return []

        results = []

        try:
            # Bước 1: Trích xuất embedding từ tất cả khuôn mặt trong frame
            embeddings_data = DeepFace.represent(
                img_path=frame,
                model_name=model_name,
                detector_backend=detector_backend,
                enforce_detection=False,
                align=True,
                anti_spoofing=anti_spoofing,
            )

            # DeepFace trả về list of dict
            if not isinstance(embeddings_data, list):
                return []

            for face_data in embeddings_data:
                embedding = np.array(face_data.get('embedding', []), dtype=np.float32)

                if embedding.size == 0:
                    continue

                # L2 normalize
                norm = np.linalg.norm(embedding)
                if norm > 0:
                    embedding = embedding / norm

                # Lấy tọa độ bounding box
                facial_area = face_data.get('facial_area', {})
                x = facial_area.get('x', 0)
                y = facial_area.get('y', 0)
                w = facial_area.get('w', 0)
                h = facial_area.get('h', 0)
                bbox = [x, y, x + w, y + h]

                confidence = face_data.get('face_confidence', 0.99)

                result_item = {
                    'bbox': bbox,
                    'embedding': embedding,
                    'confidence': float(confidence),
                }

                # Thêm thông tin anti-spoofing nếu được bật
                if anti_spoofing:
                    result_item['is_real'] = face_data.get('is_real', True)
                    result_item['antispoof_score'] = face_data.get('antispoof_score', 1.0)

                results.append(result_item)

        except Exception as e:
            err_msg = str(e)
            if "Spoof detected" in err_msg:
                # Anti-spoofing reject ảnh tĩnh → thử lại KHÔNG có anti-spoofing
                # để vẫn lấy được embedding (cần thiết khi training từ file ảnh)
                try:
                    embeddings_data = DeepFace.represent(
                        img_path=frame,
                        model_name=model_name,
                        detector_backend=detector_backend,
                        enforce_detection=False,
                        align=True,
                        anti_spoofing=False,
                    )
                    if isinstance(embeddings_data, list):
                        for face_data in embeddings_data:
                            embedding = np.array(face_data.get('embedding', []), dtype=np.float32)
                            if embedding.size == 0:
                                continue
                            norm = np.linalg.norm(embedding)
                            if norm > 0:
                                embedding = embedding / norm
                            facial_area = face_data.get('facial_area', {})
                            x = facial_area.get('x', 0)
                            y = facial_area.get('y', 0)
                            w = facial_area.get('w', 0)
                            h = facial_area.get('h', 0)
                            results.append({
                                'bbox': [x, y, x + w, y + h],
                                'embedding': embedding,
                                'confidence': float(face_data.get('face_confidence', 0.99)),
                                'is_real': False,
                                'antispoof_score': 0.0,
                            })
                except Exception:
                    pass
            elif "Face could not be detected" not in err_msg:
                print(f"[ENGINE DeepFace LỖI] {e}")

        return results

    def analyze_face(frame, actions=('age', 'gender', 'emotion')):
        """
        Phân tích thuộc tính khuôn mặt (tuổi, giới tính, cảm xúc, sắc tộc).

        Args:
            frame: numpy array BGR từ OpenCV
            actions: Tuple các thuộc tính cần phân tích.
                Options: 'age', 'gender', 'emotion', 'race'

        Returns:
            list[dict]: [{
                'bbox': [x1, y1, x2, y2],
                'age': float,
                'gender': str,
                'dominant_emotion': str,
                'emotion': dict,
                'dominant_race': str (nếu analyze race),
            }, ...]
        """
        if frame is None or frame.size == 0:
            return []

        try:
            analysis = DeepFace.analyze(
                img_path=frame,
                actions=actions,
                detector_backend=detector_backend,
                enforce_detection=False,
                align=True,
                silent=True,
                anti_spoofing=anti_spoofing,
            )

            if not isinstance(analysis, list):
                return []

            results = []
            for face_info in analysis:
                region = face_info.get('region', {})
                x = region.get('x', 0)
                y = region.get('y', 0)
                w = region.get('w', 0)
                h = region.get('h', 0)

                result_item = {
                    'bbox': [x, y, x + w, y + h],
                }

                if 'age' in actions:
                    result_item['age'] = face_info.get('age', 0)

                if 'gender' in actions:
                    result_item['gender'] = face_info.get('dominant_gender', 'Unknown')
                    result_item['gender_scores'] = face_info.get('gender', {})

                if 'emotion' in actions:
                    result_item['dominant_emotion'] = face_info.get('dominant_emotion', 'neutral')
                    result_item['emotion'] = face_info.get('emotion', {})

                if 'race' in actions:
                    result_item['dominant_race'] = face_info.get('dominant_race', 'Unknown')
                    result_item['race'] = face_info.get('race', {})

                results.append(result_item)

            return results

        except Exception as e:
            if "Face could not be detected" not in str(e):
                print(f"[ENGINE DeepFace ANALYZE LỖI] {e}")
            return []

    def verify_liveness(frame):
        """
        Kiểm tra khuôn mặt thật hay giả (anti-spoofing).

        Args:
            frame: numpy array BGR

        Returns:
            list[dict]: [{
                'bbox': [x1, y1, x2, y2],
                'is_real': bool,
                'antispoof_score': float,
                'confidence': float,
            }, ...]
        """
        if frame is None or frame.size == 0:
            return []

        try:
            face_objs = DeepFace.extract_faces(
                img_path=frame,
                detector_backend=detector_backend,
                enforce_detection=False,
                anti_spoofing=True,
            )

            results = []
            for face_obj in face_objs:
                facial_area = face_obj.get('facial_area', {})
                x = facial_area.get('x', 0)
                y = facial_area.get('y', 0)
                w = facial_area.get('w', 0)
                h = facial_area.get('h', 0)

                results.append({
                    'bbox': [x, y, x + w, y + h],
                    'is_real': face_obj.get('is_real', True),
                    'antispoof_score': face_obj.get('antispoof_score', 1.0),
                    'confidence': face_obj.get('confidence', 0.0),
                })

            return results

        except Exception as e:
            if "Face could not be detected" not in str(e):
                print(f"[ENGINE DeepFace LIVENESS LỖI] {e}")
            return []

    def verify_two_faces(img1, img2, threshold=None):
        """
        So sánh 2 khuôn mặt xem có phải cùng 1 người không.
        Hữu ích cho mobile check-in (so ảnh selfie với ảnh đăng ký).

        Args:
            img1: numpy array BGR hoặc đường dẫn file ảnh 1
            img2: numpy array BGR hoặc đường dẫn file ảnh 2
            threshold: Ngưỡng khoảng cách (None = dùng mặc định của model)

        Returns:
            dict: {
                'verified': bool,
                'distance': float,
                'threshold': float,
                'confidence': float,
                'model': str,
            }
        """
        try:
            result = DeepFace.verify(
                img1_path=img1,
                img2_path=img2,
                model_name=model_name,
                detector_backend=detector_backend,
                distance_metric='cosine',
                enforce_detection=False,
                align=True,
                threshold=threshold,
                anti_spoofing=anti_spoofing,
            )
            return {
                'verified': result.get('verified', False),
                'distance': result.get('distance', 1.0),
                'threshold': result.get('threshold', 0.4),
                'confidence': result.get('confidence', 0.0),
                'model': model_name,
            }
        except Exception as e:
            print(f"[ENGINE DeepFace VERIFY LỖI] {e}")
            return {
                'verified': False,
                'distance': 1.0,
                'threshold': 0.4,
                'confidence': 0.0,
                'model': model_name,
                'error': str(e),
            }

    return {
        'name': f'DeepFace ({model_name} + {detector_backend})',
        'embedding_dim': embedding_dim,
        'detect_and_embed': detect_and_embed,
        'analyze_face': analyze_face,
        'verify_liveness': verify_liveness,
        'verify_two_faces': verify_two_faces,
        'model_name': model_name,
        'detector_backend': detector_backend,
        'anti_spoofing': anti_spoofing,
    }
