import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, transforms, models
from torch.utils.data import DataLoader, random_split
import os
import matplotlib.pyplot as plt
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix
import numpy as np
import seaborn as sns

class FaceResNet(nn.Module):
    def __init__(self, num_classes, feature_dim=512):
        super(FaceResNet, self).__init__()
        # Sử dụng mô hình ResNet50 pretrained
        self.resnet = models.resnet50(pretrained=True)
        
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

def train_and_evaluate():
    # 1. Tham số hệ thống
    batch_size = 32
    num_epochs = 20
    learning_rate = 0.001
    dataset_path = "database" # THAY ĐỔI ĐƯỜNG DẪN Ở ĐÂY
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"[*] Sử dụng thiết bị: {device}")

    # 2. Tiền xử lý dữ liệu (Augmentation & Normalization)
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(),
        transforms.ColorJitter(brightness=0.2, contrast=0.2),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    if not os.path.exists(dataset_path):
        print(f"[!] Lỗi: Không tìm thấy thư mục dataset '{dataset_path}'")
        return

    # 3. Load Dataset & Chia Train/Validation (80/20)
    full_dataset = datasets.ImageFolder(root=dataset_path, transform=transform)
    num_classes = len(full_dataset.classes)
    class_names = full_dataset.classes
    
    train_size = int(0.8 * len(full_dataset))
    val_size = len(full_dataset) - train_size
    train_dataset, val_dataset = random_split(full_dataset, [train_size, val_size])

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=2)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=2)

    # 4. Khởi tạo mô hình
    model = FaceResNet(num_classes=num_classes).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)

    # Biến lưu trữ lịch sử để vẽ biểu đồ
    history = {'train_loss': [], 'val_loss': [], 'train_acc': [], 'val_acc': []}

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
        all_preds = []
        all_labels = []
        
        with torch.no_grad():
            for images, labels in val_loader:
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                loss = criterion(outputs, labels)
                
                val_loss += loss.item()
                _, predicted = outputs.max(1)
                val_total += labels.size(0)
                val_correct += predicted.eq(labels).sum().item()
                
                all_preds.extend(predicted.cpu().numpy())
                all_labels.extend(labels.cpu().numpy())

        val_loss = val_loss / len(val_loader)
        val_acc = 100. * val_correct / val_total
        
        history['train_loss'].append(train_loss)
        history['val_loss'].append(val_loss)
        history['train_acc'].append(train_acc)
        history['val_acc'].append(val_acc)

        print(f"Epoch [{epoch+1}/{num_epochs}] - "
              f"Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.2f}% | "
              f"Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.2f}%")

    # 6. Tính toán các chỉ số Báo cáo (Precision, Recall, F1-Score)
    print("\n" + "="*50)
    print("[*] TỔNG HỢP CÁC CHỈ SỐ BÁO CÁO (VALIDATION TẬP CUỐI):")
    precision = precision_score(all_labels, all_preds, average='macro', zero_division=0)
    recall = recall_score(all_labels, all_preds, average='macro', zero_division=0)
    f1 = f1_score(all_labels, all_preds, average='macro', zero_division=0)
    
    print(f" - Độ chính xác tổng thể (Accuracy): {val_acc:.2f}%")
    print(f" - Precision (Độ chuẩn xác): {precision:.4f}")
    print(f" - Recall (Độ phủ): {recall:.4f}")
    print(f" - F1-Score: {f1:.4f}")
    print("="*50)

    # 7. Vẽ biểu đồ Loss và Accuracy để đưa vào báo cáo
    os.makedirs('reports', exist_ok=True)
    
    plt.figure(figsize=(12, 5))
    # Biểu đồ Accuracy
    plt.subplot(1, 2, 1)
    plt.plot(history['train_acc'], label='Train Accuracy')
    plt.plot(history['val_acc'], label='Validation Accuracy')
    plt.title('Đồ thị Accuracy (Độ chính xác)')
    plt.xlabel('Epochs')
    plt.ylabel('Accuracy (%)')
    plt.legend()
    plt.grid(True)

    # Biểu đồ Loss
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
    
    # 8. Vẽ Ma trận nhầm lẫn (Confusion Matrix)
    cm = confusion_matrix(all_labels, all_preds)
    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=class_names, yticklabels=class_names)
    plt.title('Confusion Matrix (Ma trận nhầm lẫn)')
    plt.ylabel('Nhãn thực tế (True Label)')
    plt.xlabel('Nhãn dự đoán (Predicted Label)')
    plt.tight_layout()
    plt.savefig('reports/resnet_confusion_matrix.png')
    print("[*] Đã lưu ma trận nhầm lẫn tại: reports/resnet_confusion_matrix.png")

    # 9. Lưu mô hình
    torch.save(model.state_dict(), 'resnet_face_model.pth')
    print("[*] Đã lưu trọng số mô hình: resnet_face_model.pth")

if __name__ == "__main__":
    train_and_evaluate()
