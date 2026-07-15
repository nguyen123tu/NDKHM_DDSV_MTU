import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, transforms, models
from torch.utils.data import DataLoader, Subset
import os
import random
import copy
import matplotlib.pyplot as plt
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix
import numpy as np
import seaborn as sns

# =====================================================================
# GHI CHÚ QUAN TRỌNG (đọc trước khi chạy):
# Dataset của bạn rất nhỏ (13 người, ~10 ảnh/người). Với dữ liệu ít như
# vậy, random_split() theo ảnh rất dễ khiến các ảnh gần giống hệt nhau
# (cùng buổi chụp, cùng ánh sáng, cùng góc) bị chia vào cả train và
# validation -> val accuracy ảo cao (ví dụ 100%) nhưng không phản ánh
# đúng khả năng nhận diện thực tế.
#
# Script này chia dữ liệu THEO TỪNG NGƯỜI (per-class), với 1 tập TEST
# hoàn toàn tách biệt, không được dùng trong lúc train, chỉ dùng để
# đánh giá cuối cùng -> số liệu báo cáo đáng tin cậy hơn.
# =====================================================================

SEED = 42
random.seed(SEED)
torch.manual_seed(SEED)
np.random.seed(SEED)


class FaceResNet(nn.Module):
    def __init__(self, num_classes, feature_dim=512):
        super(FaceResNet, self).__init__()
        # Sử dụng mô hình ResNet50 pretrained
        self.resnet = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V1)

        # Tùy chỉnh lớp FC để trả về vector đặc trưng (chỉ số khuôn mặt)
        num_ftrs = self.resnet.fc.in_features
        self.resnet.fc = nn.Sequential(
            nn.Linear(num_ftrs, feature_dim),
            nn.BatchNorm1d(feature_dim),
            nn.PReLU()
        )

        self.classifier = nn.Linear(feature_dim, num_classes)

    def forward(self, x, return_features=False):
        features = self.resnet(x)
        if return_features:
            return features
        logits = self.classifier(features)
        return logits


def split_dataset_per_class(full_dataset, test_ratio=0.2, val_ratio=0.1,
                             min_test=1, min_val=1, min_train=3):
    """
    Chia dữ liệu THEO TỪNG LỚP (từng người), TỰ ĐỘNG thích ứng theo số
    ảnh thực tế của mỗi người (vì số ảnh mỗi người có thể không đều
    nhau, ví dụ người 8 ảnh, người 15 ảnh...).

    Quy tắc cho mỗi người:
      - test  = round(test_ratio * n_total), tối thiểu `min_test` ảnh
      - val   = round(val_ratio  * n_total), tối thiểu `min_val` ảnh
      - train = phần còn lại, PHẢI còn tối thiểu `min_train` ảnh

    Nếu người nào không đủ ảnh để đảm bảo tối thiểu train/val/test,
    hàm sẽ ưu tiên giữ đủ train trước, giảm val/test và in cảnh báo
    để bạn biết người đó cần thu thêm ảnh.
    """
    targets = np.array(full_dataset.targets)
    train_idx, val_idx, test_idx = [], [], []
    warnings_list = []

    print("\n[*] Số ảnh theo từng người:")
    for class_idx, class_name in enumerate(full_dataset.classes):
        class_indices = np.where(targets == class_idx)[0].tolist()
        random.shuffle(class_indices)
        n_total = len(class_indices)
        print(f"    - {class_name}: {n_total} ảnh")

        n_test = max(min_test, round(n_total * test_ratio))
        n_val = max(min_val, round(n_total * val_ratio))

        # Đảm bảo vẫn còn đủ ảnh cho train, nếu không thì giảm bớt val/test
        while n_total - n_test - n_val < min_train and (n_test > 0 or n_val > 0):
            if n_val > 0:
                n_val -= 1
            elif n_test > 0:
                n_test -= 1

        n_train = n_total - n_test - n_val

        if n_train < min_train or n_test < 1:
            warnings_list.append(
                f"'{class_name}' chỉ có {n_total} ảnh -> train={n_train}, val={n_val}, "
                f"test={n_test} (quá ít, nên thu thêm ảnh cho người này)"
            )

        test_idx.extend(class_indices[:n_test])
        val_idx.extend(class_indices[n_test:n_test + n_val])
        train_idx.extend(class_indices[n_test + n_val:])

    if warnings_list:
        print("\n[!] CẢNH BÁO - các lớp có số ảnh quá ít, kết quả cho lớp này dễ sai số:")
        for w in warnings_list:
            print(f"    - {w}")

    return train_idx, val_idx, test_idx


class TransformSubset(torch.utils.data.Dataset):
    """Cho phép áp dụng transform khác nhau cho từng subset (train cần augmentation
    mạnh, val/test chỉ cần resize + normalize, không augmentation)."""
    def __init__(self, dataset_path, indices, transform):
        self.samples_dataset = datasets.ImageFolder(root=dataset_path)
        self.indices = indices
        self.transform = transform

    def __len__(self):
        return len(self.indices)

    def __getitem__(self, i):
        path, label = self.samples_dataset.samples[self.indices[i]]
        image = self.samples_dataset.loader(path)
        if self.transform:
            image = self.transform(image)
        return image, label


def train_and_evaluate():
    # 1. Tham số hệ thống
    batch_size = 8            # giảm batch size vì dataset rất nhỏ
    num_epochs = 30
    learning_rate = 0.0001
    patience = 7               # early stopping: dừng nếu val_loss không cải thiện sau N epoch
    dataset_path = os.path.join(os.path.dirname(__file__), "..", "database")  # THAY ĐỔI ĐƯỜNG DẪN Ở ĐÂY

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"[*] Sử dụng thiết bị: {device}")

    if not os.path.exists(dataset_path):
        print(f"[!] Lỗi: Không tìm thấy thư mục dataset '{dataset_path}'")
        return

    # 2. Tiền xử lý dữ liệu
    # -- Augmentation MẠNH cho tập train (bù cho dataset nhỏ) --
    train_transform = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.RandomResizedCrop(224, scale=(0.8, 1.0)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(15),
        transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.2),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        transforms.RandomErasing(p=0.2),
    ])

    # -- Val/Test: KHÔNG augmentation, chỉ resize + normalize --
    eval_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    # 3. Load Dataset & Chia Train/Val/Test THEO TỪNG NGƯỜI
    base_dataset = datasets.ImageFolder(root=dataset_path)
    num_classes = len(base_dataset.classes)
    class_names = base_dataset.classes
    print(f"[*] Tổng số người (lớp): {num_classes}")
    print(f"[*] Tổng số ảnh: {len(base_dataset)}")

    train_idx, val_idx, test_idx = split_dataset_per_class(
        base_dataset,
        test_ratio=0.2,    # ~20% ảnh mỗi người dành cho test
        val_ratio=0.1,     # ~10% ảnh mỗi người dành cho val
        min_test=1,        # tối thiểu 1 ảnh/người cho test dù ratio ra 0
        min_val=1,         # tối thiểu 1 ảnh/người cho val
        min_train=3,       # cần tối thiểu 3 ảnh/người để train mới có ý nghĩa
    )
    print(f"\n[*] Tổng số ảnh train: {len(train_idx)} | val: {len(val_idx)} | test: {len(test_idx)}")

    train_dataset = TransformSubset(dataset_path, train_idx, train_transform)
    val_dataset = TransformSubset(dataset_path, val_idx, eval_transform)
    test_dataset = TransformSubset(dataset_path, test_idx, eval_transform)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=0)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False, num_workers=0)

    # 4. Khởi tạo mô hình
    model = FaceResNet(num_classes=num_classes).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=3)

    history = {'train_loss': [], 'val_loss': [], 'train_acc': [], 'val_acc': []}

    best_val_loss = float('inf')
    best_model_state = None
    epochs_no_improve = 0

    # 5. Vòng lặp huấn luyện (Training Loop)
    print("\n[*] Bắt đầu huấn luyện...")
    for epoch in range(num_epochs):
        # -- Phase Train --
        model.train()
        running_loss, correct, total = 0.0, 0, 0
        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            running_loss += loss.item()
            _, predicted = outputs.max(1)
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()

        train_loss = running_loss / len(train_loader)
        train_acc = 100. * correct / total

        # -- Phase Validation --
        model.eval()
        val_loss, val_correct, val_total = 0.0, 0, 0
        with torch.no_grad():
            for images, labels in val_loader:
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                loss = criterion(outputs, labels)

                val_loss += loss.item()
                _, predicted = outputs.max(1)
                val_total += labels.size(0)
                val_correct += predicted.eq(labels).sum().item()

        val_loss = val_loss / len(val_loader)
        val_acc = 100. * val_correct / val_total

        scheduler.step(val_loss)

        history['train_loss'].append(train_loss)
        history['val_loss'].append(val_loss)
        history['train_acc'].append(train_acc)
        history['val_acc'].append(val_acc)

        print(f"Epoch [{epoch+1}/{num_epochs}] - "
              f"Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.2f}% | "
              f"Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.2f}%")

        # -- Early stopping dựa trên val_loss --
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_model_state = copy.deepcopy(model.state_dict())
            epochs_no_improve = 0
        else:
            epochs_no_improve += 1
            if epochs_no_improve >= patience:
                print(f"[*] Early stopping tại epoch {epoch+1} (val_loss không cải thiện sau {patience} epoch)")
                break

    # Khôi phục lại trọng số tốt nhất (theo val_loss) trước khi đánh giá trên test
    if best_model_state is not None:
        model.load_state_dict(best_model_state)
        print(f"[*] Đã khôi phục mô hình tốt nhất (val_loss = {best_val_loss:.4f})")

    # 6. ĐÁNH GIÁ TRÊN TẬP TEST ĐỘC LẬP (chưa từng được dùng trong lúc train)
    print("\n" + "="*50)
    print("[*] ĐÁNH GIÁ TRÊN TẬP TEST ĐỘC LẬP (không dùng trong quá trình huấn luyện):")
    model.eval()
    test_correct, test_total = 0, 0
    all_preds, all_labels = [], []
    with torch.no_grad():
        for images, labels in test_loader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            _, predicted = outputs.max(1)
            test_total += labels.size(0)
            test_correct += predicted.eq(labels).sum().item()
            all_preds.extend(predicted.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())

    test_acc = 100. * test_correct / test_total
    precision = precision_score(all_labels, all_preds, average='macro', zero_division=0)
    recall = recall_score(all_labels, all_preds, average='macro', zero_division=0)
    f1 = f1_score(all_labels, all_preds, average='macro', zero_division=0)

    print(f" - Số ảnh test: {test_total}")
    print(f" - Độ chính xác trên tập test (Accuracy): {test_acc:.2f}%")
    print(f" - Precision (Độ chuẩn xác): {precision:.4f}")
    print(f" - Recall (Độ phủ): {recall:.4f}")
    print(f" - F1-Score: {f1:.4f}")
    print("="*50)
    print("[!] LƯU Ý: Dataset chỉ có ~10 ảnh/người (13 người), số liệu trên mang tính")
    print("    minh hoạ (proof of concept), nên nêu rõ hạn chế này trong báo cáo.")

    # 7. Vẽ biểu đồ Loss và Accuracy để đưa vào báo cáo
    os.makedirs('reports', exist_ok=True)

    plt.figure(figsize=(12, 5))
    plt.subplot(1, 2, 1)
    plt.plot(history['train_acc'], label='Train Accuracy')
    plt.plot(history['val_acc'], label='Validation Accuracy')
    plt.title('Đồ thị Accuracy (Độ chính xác)')
    plt.xlabel('Epochs')
    plt.ylabel('Accuracy (%)')
    plt.legend()
    plt.grid(True)

    plt.subplot(1, 2, 2)
    plt.plot(history['train_loss'], label='Train Loss')
    plt.plot(history['val_loss'], label='Validation Loss')
    plt.title('Đồ thị Loss (Độ mất mát)')
    plt.xlabel('Epochs')
    plt.ylabel('Loss')
    plt.legend()
    plt.grid(True)

    plt.tight_layout()
    plt.savefig('reports/resnet_training_curves.png')
    print("[*] Đã lưu đồ thị Accuracy và Loss tại: reports/resnet_training_curves.png")

    # 8. Vẽ Ma trận nhầm lẫn (Confusion Matrix) TRÊN TẬP TEST
    cm = confusion_matrix(all_labels, all_preds, labels=list(range(num_classes)))
    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=class_names, yticklabels=class_names)
    plt.title('Confusion Matrix trên tập Test (Ma trận nhầm lẫn)')
    plt.ylabel('Nhãn thực tế (True Label)')
    plt.xlabel('Nhãn dự đoán (Predicted Label)')
    plt.tight_layout()
    plt.savefig('reports/resnet_confusion_matrix.png')
    print("[*] Đã lưu ma trận nhầm lẫn tại: reports/resnet_confusion_matrix.png")

    # 9. Lưu mô hình (trọng số tốt nhất theo val_loss)
    torch.save(model.state_dict(), 'resnet_face_model.pth')
    print("[*] Đã lưu trọng số mô hình: resnet_face_model.pth")


if __name__ == "__main__":
    train_and_evaluate()