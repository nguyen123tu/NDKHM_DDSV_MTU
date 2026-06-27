import 'dart:io';
import 'package:flutter/foundation.dart';

/// Service nhận diện khuôn mặt
/// Hiện tại dùng server-side recognition (API).
/// TFLite offline sẽ được tích hợp khi có model file.
class FaceRecognitionService {
  static final FaceRecognitionService _instance = FaceRecognitionService._internal();
  factory FaceRecognitionService() => _instance;
  FaceRecognitionService._internal();

  final bool _isModelLoaded = false;

  /// Trạng thái sẵn sàng của mô hình Offline
  bool get isReady => _isModelLoaded;

  /// Khởi tạo model (placeholder - chưa có model file)
  Future<void> initModel() async {
    // TODO: Tích hợp TFLite khi có model file
    debugPrint('[FaceRecognition] Offline model chưa sẵn sàng, dùng server-side.');
  }

  /// Nhận diện offline (chưa hỗ trợ)
  Future<Map<String, dynamic>?> recognizeFaceOffline(File imageFile) async {
    return null; // Fallback sang API
  }
}
