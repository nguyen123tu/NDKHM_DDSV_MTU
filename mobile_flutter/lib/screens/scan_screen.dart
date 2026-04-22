import 'dart:async';
import 'dart:convert';
import 'dart:math';
import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import '../services/api_service.dart';

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
    _cameras = await availableCameras();
    if (_cameras != null && _cameras!.isNotEmpty) {
      final frontCamera = _cameras!.firstWhere(
        (c) => c.lensDirection == CameraLensDirection.front,
        orElse: () => _cameras![0],
      );
      _controller = CameraController(frontCamera, ResolutionPreset.low);
      await _controller!.initialize();
      if (!mounted) return;
      setState(() => _isInitialized = true);

      // Bắt đầu auto scan sau 1.5 giây
      _autoScanTimer = Timer.periodic(const Duration(seconds: 3), (_) {
        if (_autoScan && !_isScanning && mounted) {
          _captureAndRecognize();
        }
      });
    }
  }

  @override
  void dispose() {
    _autoScanTimer?.cancel();
    _controller?.dispose();
    _scanLineController.dispose();
    _cornerPulseController.dispose();
    super.dispose();
  }

  Future<void> _captureAndRecognize() async {
    if (_isScanning || _controller == null || !_controller!.value.isInitialized) return;

    setState(() {
      _isScanning = true;
      _resultSuccess = null;
      _resultName = null;
      _resultMssv = null;
      _resultMessage = null;
    });

    try {
      final image = await _controller!.takePicture();
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
          // Tạm dừng auto scan 5 giây khi nhận diện thành công
          _autoScan = false;
        });
        Future.delayed(const Duration(seconds: 5), () {
          if (mounted) setState(() => _autoScan = true);
        });
      } else {
        setState(() {
          _resultSuccess = false;
          _resultMessage = result['msg'] ?? 'Không nhận diện được khuôn mặt';
        });
        // Xóa thông báo lỗi sau 3 giây
        Future.delayed(const Duration(seconds: 3), () {
          if (mounted) setState(() { _resultSuccess = null; _resultMessage = null; });
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _resultSuccess = false;
          _resultMessage = 'Lỗi kết nối server: $e';
        });
        Future.delayed(const Duration(seconds: 3), () {
          if (mounted) setState(() { _resultSuccess = null; _resultMessage = null; });
        });
      }
    } finally {
      if (mounted) setState(() => _isScanning = false);
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
                        Text("Đang khởi tạo Camera...", style: TextStyle(color: Colors.white60)),
                      ],
                    ),
                  ),
                ),

          // Lớp phủ tối
          Positioned.fill(child: Container(color: Colors.black.withOpacity(0.35))),

          // ====== KHUNG QUÉT ======
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

          // Đường quét (luôn hiện khi auto scan đang bật)
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
                          // Chấm trạng thái
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
                            _isScanning ? "Đang nhận diện..." : _autoScan ? "Tự động quét" : "Tạm dừng",
                            style: const TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.w600),
                          ),
                        ],
                      ),
                    ),
                    const Spacer(),
                    // Toggle Auto
                    _buildGlassButton(
                      child: Icon(
                        _autoScan ? Icons.pause : Icons.play_arrow,
                        color: Colors.white,
                        size: 20,
                      ),
                      onTap: () => setState(() => _autoScan = !_autoScan),
                    ),
                  ],
                ),
              ),
            ),
          ),

          // ====== KẾT QUẢ NHẬN DIỆN ======
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

          // ====== PHẦN DƯỚI ======
          Positioned(
            bottom: 0,
            left: 0,
            right: 0,
            child: ClipRRect(
              borderRadius: const BorderRadius.vertical(top: Radius.circular(28)),
              child: BackdropFilter(
                filter: ImageFilter.blur(sigmaX: 20, sigmaY: 20),
                child: Container(
                  padding: const EdgeInsets.fromLTRB(28, 20, 28, 36),
                  decoration: BoxDecoration(
                    color: const Color(0xFF0F172A).withOpacity(0.8),
                    borderRadius: const BorderRadius.vertical(top: Radius.circular(28)),
                    border: Border(top: BorderSide(color: Colors.white.withOpacity(0.08))),
                  ),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      // Thanh kéo
                      Container(width: 40, height: 4, decoration: BoxDecoration(color: Colors.white.withOpacity(0.15), borderRadius: BorderRadius.circular(2))),
                      const SizedBox(height: 18),

                      Row(
                        children: [
                          // Trạng thái
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Text("Chế độ tự động", style: TextStyle(color: Colors.white, fontSize: 15, fontWeight: FontWeight.w600)),
                                const SizedBox(height: 4),
                                Text(
                                  "Quét mỗi 3 giây • Đặt khuôn mặt vào khung",
                                  style: TextStyle(color: Colors.white.withOpacity(0.4), fontSize: 12),
                                ),
                              ],
                            ),
                          ),
                          // Nút chụp thủ công
                          GestureDetector(
                            onTap: _isScanning ? null : _captureAndRecognize,
                            child: Container(
                              width: 56,
                              height: 56,
                              decoration: BoxDecoration(
                                shape: BoxShape.circle,
                                border: Border.all(color: _isScanning ? Colors.orange : Colors.white, width: 3),
                                boxShadow: [
                                  BoxShadow(color: const Color(0xFF2E96EB).withOpacity(0.3), blurRadius: 16),
                                ],
                              ),
                              child: Container(
                                margin: const EdgeInsets.all(3),
                                decoration: BoxDecoration(
                                  shape: BoxShape.circle,
                                  color: _isScanning ? Colors.orange : const Color(0xFF2E96EB),
                                ),
                                child: Center(
                                  child: _isScanning
                                      ? const SizedBox(width: 22, height: 22, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2.5))
                                      : const Icon(Icons.camera_alt, color: Colors.white, size: 22),
                                ),
                              ),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
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

// ====== KHUNG QUÉT 4 GÓC ======
class ScanFramePainter extends CustomPainter {
  final double pulseValue;
  final bool isScanning;
  final bool? isSuccess;

  ScanFramePainter({required this.pulseValue, required this.isScanning, this.isSuccess});

  @override
  void paint(Canvas canvas, Size size) {
    Color frameColor;
    if (isSuccess == true) {
      frameColor = const Color(0xFF10B981);
    } else if (isSuccess == false) {
      frameColor = Colors.redAccent;
    } else if (isScanning) {
      frameColor = Colors.orange;
    } else {
      frameColor = const Color(0xFF2E96EB);
    }

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

// ====== ĐƯỜNG QUÉT NGANG ======
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
