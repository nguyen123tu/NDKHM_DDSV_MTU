import 'dart:async';
import 'dart:convert';
import 'dart:math';
import 'dart:ui';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:google_mlkit_face_detection/google_mlkit_face_detection.dart';

import '../services/api_service.dart';
import '../services/face_recognition_service.dart';
import '../data/repositories/attendance_repository.dart';

class ScanScreen extends StatefulWidget {
  const ScanScreen({super.key});

  @override
  _ScanScreenState createState() => _ScanScreenState();
}

class _ScanScreenState extends State<ScanScreen> with TickerProviderStateMixin {
  CameraController? _controller;
  List<CameraDescription>? _cameras;
  bool _isInitialized = false;
  bool _isScanning = false;
  bool _autoScan = true;
  final ApiService _apiService = ApiService();
  
  // Google ML Kit Face Detector
  final FaceDetector _faceDetector = FaceDetector(
    options: FaceDetectorOptions(
      enableContours: false,
      enableLandmarks: false,
      enableClassification: false,
      performanceMode: FaceDetectorMode.fast, // Tối ưu tốc độ
    ),
  );

  // Animation
  late AnimationController _scanLineController;
  late Animation<double> _scanLineAnimation;
  late AnimationController _cornerPulseController;
  late Animation<double> _cornerPulseAnimation;

  // Kết quả
  String? _resultName;
  String? _resultMssv;
  String? _resultMessage;
  bool? _resultSuccess;

  // Auto scan timer
  Timer? _autoScanTimer;

  @override
  void initState() {
    super.initState();
    _initCamera();

    _scanLineController = AnimationController(vsync: this, duration: const Duration(milliseconds: 2500))..repeat();
    _scanLineAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _scanLineController, curve: Curves.easeInOut),
    );

    _cornerPulseController = AnimationController(vsync: this, duration: const Duration(milliseconds: 1500))..repeat(reverse: true);
    _cornerPulseAnimation = Tween<double>(begin: 0.6, end: 1.0).animate(
      CurvedAnimation(parent: _cornerPulseController, curve: Curves.easeInOut),
    );
  }

  Future<void> _initCamera() async {
    try {
      _cameras = await availableCameras();
      if (_cameras != null && _cameras!.isNotEmpty) {
        final frontCamera = _cameras!.firstWhere(
          (c) => c.lensDirection == CameraLensDirection.front,
          orElse: () => _cameras![0],
        );
        _controller = CameraController(
          frontCamera, 
          ResolutionPreset.medium, // Giảm độ phân giải để ML chạy nhanh hơn
          enableAudio: false,
        );
        await _controller!.initialize();
        if (!mounted) return;
        setState(() => _isInitialized = true);

        // Bắt đầu auto scan mỗi 1.5 giây (Tốc độ quét liên tục cực nhanh)
        _autoScanTimer = Timer.periodic(const Duration(milliseconds: 1500), (_) {
          if (_autoScan && !_isScanning && mounted) {
            _captureAndDetectFace();
          }
        });
      } else {
         throw Exception("Không tìm thấy camera");
      }
    } catch (e) {
      if (!mounted) return;
      showDialog(
        context: context,
        builder: (c) => AlertDialog(
          title: const Text("Lỗi Khởi Tạo"),
          content: Text("Không thể truy cập camera: $e"),
          actions: [TextButton(onPressed: () => Navigator.pop(c), child: const Text("Đóng"))],
        ),
      );
    }
  }

  @override
  void dispose() {
    _autoScanTimer?.cancel();
    _faceDetector.close();
    _controller?.dispose();
    _scanLineController.dispose();
    _cornerPulseController.dispose();
    super.dispose();
  }

  /// BƯỚC 1: ML Kit xử lý Offline, tìm ra Khuôn mặt trước khi làm việc nặng
  Future<void> _captureAndDetectFace() async {
    if (_isScanning || _controller == null || !_controller!.value.isInitialized) return;

    try {
      final imageFile = await _controller!.takePicture();
      final inputImage = InputImage.fromFilePath(imageFile.path);

      // Gọi ML Kit Offline siêu tốc
      final List<Face> faces = await _faceDetector.processImage(inputImage);

      if (faces.isEmpty) {
        // KHÔNG CÓ MẶT -> Im lặng quét tiếp, tiết kiệm RAM/Pin, không lag UI
        return;
      }

      // CÓ MẶT -> Chuyển sang UI đang quét & Xử lý nhận diện
      setState(() {
        _isScanning = true;
        _resultSuccess = null;
      });

      // BƯỚC 2: Xử lý Nhận Diện (Tạm thời vẫn gọi Flask API cho đến khi có file TFLite)
      await _recognizeViaApi(imageFile);

    } catch (e) {
      print('Lỗi camera/ML: $e');
    } finally {
      if (mounted) setState(() => _isScanning = false);
    }
  }

  Future<void> _recognizeViaApi(XFile image) async {
    try {
      final bytes = await image.readAsBytes();
      final base64Image = base64Encode(bytes);
      final dataUrl = "data:image/jpeg;base64,$base64Image";

      final result = await _apiService.recognizeFace(dataUrl);

      if (!mounted) return;

      if (result['success'] == true) {
        final student = result['student'];
        final att = result['attendance'];
        
        setState(() {
          _resultSuccess = true;
          _resultName = student['ho_ten'] ?? 'N/A';
          _resultMssv = student['mssv'] ?? '';
          _resultMessage = att != null ? (att['msg'] ?? 'Điểm danh thành công') : 'Nhận diện thành công';
          
          // Khi nhận ra, delay luồng auto-scan 4 giây để xem UI thành công
          _autoScan = false;
        });

        // Ghi log offline luôn cho chắc (Optional, SyncManager sẽ lo phần đẩy)
        await AttendanceRepository().saveAttendanceOffline(student['mssv'], student['do_chinh_xac'] ?? 0.99);

        Future.delayed(const Duration(seconds: 4), () {
          if (mounted) setState(() => _autoScan = true);
        });

      } else {
        setState(() {
          _resultSuccess = false;
          _resultMessage = result['msg'] ?? 'Người lạ, không nhận diện được';
        });
        Future.delayed(const Duration(seconds: 2), () {
          if (mounted) setState(() { _resultSuccess = null; _resultMessage = null; });
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _resultSuccess = false;
          _resultMessage = 'Lỗi nhận diện: $e';
        });
        Future.delayed(const Duration(seconds: 2), () {
          if (mounted) setState(() { _resultSuccess = null; _resultMessage = null; });
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(
        children: [
          // ====== CAMERA PREVIEW ======
          _isInitialized
              ? SizedBox.expand(
                  child: FittedBox(
                    fit: BoxFit.cover,
                    child: SizedBox(
                      width: _controller!.value.previewSize?.height ?? 1,
                      height: _controller!.value.previewSize?.width ?? 1,
                      child: CameraPreview(_controller!),
                    ),
                  ),
                )
              : Container(
                  color: const Color(0xFF0F172A),
                  child: const Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        CircularProgressIndicator(color: Color(0xFF2E96EB)),
                        SizedBox(height: 16),
                        Text("Đang khởi tạo Camera & ML Kit...", style: TextStyle(color: Colors.white60)),
                      ],
                    ),
                  ),
                ),

          // Lớp phủ tối
          Positioned.fill(child: Container(color: Colors.black.withOpacity(0.35))),

          // ====== KHUNG QUÉT TỰ ĐỘNG ======
          Center(
            child: AnimatedBuilder(
              animation: _cornerPulseAnimation,
              builder: (context, child) {
                return CustomPaint(
                  size: const Size(280, 350),
                  painter: ScanFramePainter(
                    pulseValue: _cornerPulseAnimation.value,
                    isScanning: _isScanning,
                    isSuccess: _resultSuccess,
                  ),
                );
              },
            ),
          ),

          // Đường quét laser
          if (_autoScan || _isScanning)
            Center(
              child: SizedBox(
                width: 280,
                height: 350,
                child: AnimatedBuilder(
                  animation: _scanLineAnimation,
                  builder: (context, child) {
                    return CustomPaint(
                      painter: ScanLinePainter(progress: _scanLineAnimation.value),
                    );
                  },
                ),
              ),
            ),

          // ====== APPBAR ======
          Positioned(
            top: 0,
            left: 0,
            right: 0,
            child: SafeArea(
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                child: Row(
                  children: [
                    _buildGlassButton(
                      child: const Icon(Icons.arrow_back_ios_new, color: Colors.white, size: 18),
                      onTap: () => Navigator.pop(context),
                    ),
                    const SizedBox(width: 10),
                    _buildGlassContainer(
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Container(
                            width: 8,
                            height: 8,
                            decoration: BoxDecoration(
                              color: _isScanning
                                  ? Colors.orange
                                  : _autoScan
                                      ? const Color(0xFF10B981)
                                      : Colors.white54,
                              shape: BoxShape.circle,
                              boxShadow: [
                                BoxShadow(
                                  color: (_isScanning ? Colors.orange : const Color(0xFF10B981)).withOpacity(0.6),
                                  blurRadius: 6,
                                ),
                              ],
                            ),
                          ),
                          const SizedBox(width: 8),
                          Text(
                            _isScanning ? "Đang phân tích AI..." : _autoScan ? "Chờ khuôn mặt" : "Tạm dừng",
                            style: const TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.w600),
                          ),
                        ],
                      ),
                    ),
                    const Spacer(),
                    // Nút On/Off AI
                    _buildGlassButton(
                      child: Icon(
                        _autoScan ? Icons.pause : Icons.smart_toy,
                        color: _autoScan ? Colors.white : Colors.blueAccent,
                        size: 20,
                      ),
                      onTap: () => setState(() => _autoScan = !_autoScan),
                    ),
                  ],
                ),
              ),
            ),
          ),

          // ====== KẾT QUẢ HIỂN THỊ (GLASSMORPHISM) ======
          if (_resultSuccess != null)
            Positioned(
              top: MediaQuery.of(context).padding.top + 64,
              left: 16,
              right: 16,
              child: ClipRRect(
                borderRadius: BorderRadius.circular(16),
                child: BackdropFilter(
                  filter: ImageFilter.blur(sigmaX: 12, sigmaY: 12),
                  child: Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: (_resultSuccess == true ? const Color(0xFF10B981) : Colors.redAccent).withOpacity(0.2),
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(
                        color: (_resultSuccess == true ? const Color(0xFF10B981) : Colors.redAccent).withOpacity(0.4),
                      ),
                    ),
                    child: Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.all(10),
                          decoration: BoxDecoration(
                            color: Colors.white.withOpacity(0.15),
                            shape: BoxShape.circle,
                          ),
                          child: Icon(
                            _resultSuccess == true ? Icons.check_circle : Icons.error_outline,
                            color: Colors.white,
                            size: 26,
                          ),
                        ),
                        const SizedBox(width: 14),
                        Expanded(
                          child: Column(
                           crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              if (_resultName != null)
                                Text(_resultName!, style: const TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold)),
                              if (_resultMssv != null)
                                Text("MSSV: $_resultMssv", style: const TextStyle(color: Colors.white70, fontSize: 12)),
                              if (_resultMessage != null)
                                Text(_resultMessage!, style: const TextStyle(color: Colors.white60, fontSize: 12)),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
            
          // Nút chụp thủ công ở dưới cùng
          Positioned(
             bottom: 30,
             left: 0,
             right: 0,
             child: Center(
               child: GestureDetector(
                 onTap: _isScanning ? null : _captureAndDetectFace,
                 child: Container(
                   width: 64,
                   height: 64,
                   decoration: BoxDecoration(
                     shape: BoxShape.circle,
                     border: Border.all(color: Colors.white, width: 3),
                   ),
                   child: Container(
                     margin: const EdgeInsets.all(4),
                     decoration: const BoxDecoration(shape: BoxShape.circle, color: Color(0xFF2E96EB)),
                     child: const Icon(Icons.camera, color: Colors.white, size: 28),
                   ),
                 ),
               ),
             ),
          )
        ],
      ),
    );
  }

  Widget _buildGlassButton({required Widget child, required VoidCallback onTap}) {
    return GestureDetector(
      onTap: onTap,
      child: ClipRRect(
        borderRadius: BorderRadius.circular(12),
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
          child: Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.15),
              borderRadius: BorderRadius.circular(12),
            ),
            child: child,
          ),
        ),
      ),
    );
  }

  Widget _buildGlassContainer({required Widget child}) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(12),
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
          decoration: BoxDecoration(
            color: Colors.white.withOpacity(0.15),
            borderRadius: BorderRadius.circular(12),
          ),
          child: child,
        ),
      ),
    );
  }
}

class ScanFramePainter extends CustomPainter {
  final double pulseValue;
  final bool isScanning;
  final bool? isSuccess;

  ScanFramePainter({required this.pulseValue, required this.isScanning, this.isSuccess});

  @override
  void paint(Canvas canvas, Size size) {
    Color frameColor;
    if (isSuccess == true) frameColor = const Color(0xFF10B981);
    else if (isSuccess == false) frameColor = Colors.redAccent;
    else if (isScanning) frameColor = Colors.orange;
    else frameColor = const Color(0xFF2E96EB);

    final cornerLength = size.width * 0.15;
    final radius = 20.0;

    final paint = Paint()
      ..color = frameColor.withOpacity(pulseValue)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 3.5
      ..strokeCap = StrokeCap.round;

    final glowPaint = Paint()
      ..color = frameColor.withOpacity(0.2 * pulseValue)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 8.0
      ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 10);

    _drawCorners(canvas, size, paint, cornerLength, radius);
    _drawCorners(canvas, size, glowPaint, cornerLength, radius);
  }

  void _drawCorners(Canvas canvas, Size size, Paint paint, double cl, double r) {
    final w = size.width, h = size.height;

    canvas.drawPath(Path()..moveTo(0, cl)..lineTo(0, r)..arcToPoint(Offset(r, 0), radius: Radius.circular(r))..lineTo(cl, 0), paint);
    canvas.drawPath(Path()..moveTo(w - cl, 0)..lineTo(w - r, 0)..arcToPoint(Offset(w, r), radius: Radius.circular(r))..lineTo(w, cl), paint);
    canvas.drawPath(Path()..moveTo(0, h - cl)..lineTo(0, h - r)..arcToPoint(Offset(r, h), radius: Radius.circular(r))..lineTo(cl, h), paint);
    canvas.drawPath(Path()..moveTo(w - cl, h)..lineTo(w - r, h)..arcToPoint(Offset(w, h - r), radius: Radius.circular(r))..lineTo(w, h - cl), paint);
  }

  @override
  bool shouldRepaint(covariant ScanFramePainter old) =>
      old.pulseValue != pulseValue || old.isScanning != isScanning || old.isSuccess != isSuccess;
}

class ScanLinePainter extends CustomPainter {
  final double progress;
  ScanLinePainter({required this.progress});

  @override
  void paint(Canvas canvas, Size size) {
    final y = size.height * progress;

    canvas.drawRect(
      Rect.fromLTWH(0, y - 1, size.width, 2),
      Paint()
        ..shader = LinearGradient(
          colors: [Colors.transparent, const Color(0xFF2E96EB).withOpacity(0.8), Colors.transparent],
          stops: const [0.0, 0.5, 1.0],
        ).createShader(Rect.fromLTWH(0, y - 1, size.width, 2)),
    );

    canvas.drawRect(
      Rect.fromLTWH(0, max(0, y - 50), size.width, 50),
      Paint()
        ..shader = LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [Colors.transparent, const Color(0xFF2E96EB).withOpacity(0.12)],
        ).createShader(Rect.fromLTWH(0, max(0, y - 50), size.width, 50)),
    );
  }

  @override
  bool shouldRepaint(covariant ScanLinePainter old) => old.progress != progress;
}
