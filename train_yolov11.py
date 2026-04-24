from ultralytics import YOLO
import os

def train_yolov11():
    # 1. Đường dẫn tới file cấu hình dataset (data.yaml)
    # File data.yaml cần định nghĩa đường dẫn train, val, nc (số class), và names (tên class)
    dataset_yaml = "data.yaml" # Thay đổi thành đường dẫn thực tế của bạn
    
    if not os.path.exists(dataset_yaml):
        print(f"Không tìm thấy file cấu hình {dataset_yaml}.")
        print("Vui lòng tạo file data.yaml theo chuẩn của YOLO.")
        return

    print("Bắt đầu khởi tạo model YOLOv11...")
    
    # 2. Khởi tạo model YOLOv11
    # Tải pretrained model YOLOv11n (nano) cho nhẹ và nhanh, có thể đổi thành yolo11s.pt, yolo11m.pt...
    model = YOLO("yolo11n.pt")

    # 3. Tiến hành training
    print("Bắt đầu quá trình training...")
    results = model.train(
        data=dataset_yaml,      # Đường dẫn tới file dataset yaml
        epochs=100,             # Số lượng epoch
        imgsz=640,              # Kích thước ảnh đầu vào
        batch=16,               # Kích thước batch
        device=0,               # Chỉ định GPU id (vd: 0), dùng 'cpu' nếu không có GPU
        project="runs/detect",  # Thư mục lưu kết quả
        name="yolov11_custom",  # Tên run
        pretrained=True,        # Sử dụng pretrained weights
        optimizer='auto',       # Optimizer tự động (SGD/AdamW)
        patience=50,            # Early stopping patience
        save=True               # Lưu lại best weights
    )

    print("Training hoàn tất. Model tốt nhất được lưu tại thư mục runs/detect/yolov11_custom/weights/best.pt")

    # 4. Đánh giá model (Validation)
    print("Bắt đầu đánh giá mô hình trên tập validation...")
    metrics = model.val()
    print(f"mAP50-95: {metrics.box.map}")    # Mean Average Precision
    print(f"mAP50: {metrics.box.map50}")     # mAP tại IoU 0.50

if __name__ == "__main__":
    train_yolov11()
