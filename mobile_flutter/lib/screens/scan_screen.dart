import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:math';
import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import 'package:google_mlkit_face_detection/google_mlkit_face_detection.dart';
import 'package:flutter_animate/flutter_animate.dart';

import '../services/api_service.dart';
import '../data/repositories/attendance_repository.dart';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:geolocator/geolocator.dart';
import '../theme/app_theme.dart';
import '../utils/camera_utils.dart';

// Liveness Detection State
enum LivenessState { findFace, challenge, returnFrontal, passed }
enum LivenessChallenge { turnLeft, turnRight, smile, blink }

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
  DateTime _lastFrameProcessed = DateTime.now();
  final ApiService _apiService = ApiService();
  bool _isOffline = false;
  bool _isProcessingFrame = false;
  double _uploadProgress = 0.0;
  String _realtimeWarning = "";
  
  final FaceDetector _faceDetector = FaceDetector(
    options: FaceDetectorOptions(
      enableContours: false,
      enableLandmarks: false,
      enableClassification: true, // Bật để nhận diện chớp mắt và nụ cười
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

  LivenessState _livenessState = LivenessState.findFace;
  LivenessChallenge _currentChallenge = LivenessChallenge.blink;

  void _resetLiveness() {
    _livenessState = LivenessState.findFace;
    final challenges = [LivenessChallenge.turnLeft, LivenessChallenge.turnRight, LivenessChallenge.smile, LivenessChallenge.blink];
    _currentChallenge = challenges[Random().nextInt(challenges.length)];
  }

  @override
  void initState() {
    super.initState();
    _resetLiveness();
    _initCamera();
    _checkConnectivity();

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
          ResolutionPreset.medium, // Giảm xuống medium (480p) để tăng FPS và giảm giật lag UI
          enableAudio: false,
          imageFormatGroup: Platform.isAndroid ? ImageFormatGroup.yuv420 : ImageFormatGroup.bgra8888,
        );
        await _controller!.initialize();
        if (!mounted) return;
        
        // Bật tự động lấy nét và tự động phơi sáng
        await _controller!.setFocusMode(FocusMode.auto);
        await _controller!.setExposureMode(ExposureMode.auto);

        setState(() {
          _isInitialized = true;
          _realtimeWarning = "Vui lòng đưa khuôn mặt vào khung";
        });

        // Bắt đầu ImageStream để nhận diện realtime
        _controller!.startImageStream((CameraImage image) {
          if (_autoScan && !_isScanning && mounted) {
            _processCameraImage(image, frontCamera);
          }
        });
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

  Future<void> _processCameraImage(CameraImage image, CameraDescription camera) async {
    if (_isProcessingFrame || _isScanning) return;
    
    // Throttle để chỉ xử lý 5-7 khung hình / giây, nhường CPU cho UI render mượt hơn
    if (DateTime.now().difference(_lastFrameProcessed).inMilliseconds < 150) return;
    
    _isProcessingFrame = true;
    _lastFrameProcessed = DateTime.now();

    try {
      if (CameraUtils.isImageTooDark(image)) {
        if (mounted) setState(() => _realtimeWarning = "Thiếu sáng! Hãy tìm nơi sáng hơn");
        _isProcessingFrame = false;
        return;
      }

      final inputImage = CameraUtils.convertCameraImageToInputImage(image, camera);
      if (inputImage == null) {
        _isProcessingFrame = false;
        return;
      }

      final faces = await _faceDetector.processImage(inputImage);
      if (faces.isEmpty) {
        if (mounted) setState(() => _realtimeWarning = "Không tìm thấy khuôn mặt");
        _isProcessingFrame = false;
        return;
      }

      final face = faces.first; // Lấy khuôn mặt to nhất (gần nhất)
      
      final rotY = face.headEulerAngleY ?? 0;
      final rotZ = face.headEulerAngleZ ?? 0;
      final leftEyeOpen = face.leftEyeOpenProbability ?? 1.0;
      final rightEyeOpen = face.rightEyeOpenProbability ?? 1.0;
      final smiling = face.smilingProbability ?? 0.0;

      // Kiểm tra khoảng cách
      final screenWidth = MediaQuery.of(context).size.width;
      if (face.boundingBox.width < screenWidth * 0.3) {
        if (mounted) setState(() => _realtimeWarning = "Hãy di chuyển lại gần hơn");
        _isProcessingFrame = false;
        return;
      }

      // STATE MACHINE: Liveness Detection
      if (_livenessState == LivenessState.findFace) {
         if (rotY.abs() <= 10 && rotZ.abs() <= 10) {
            _livenessState = LivenessState.challenge;
         } else {
            if (mounted) setState(() => _realtimeWarning = "Vui lòng nhìn thẳng camera");
            _isProcessingFrame = false;
            return;
         }
      }

      if (_livenessState == LivenessState.challenge) {
         switch (_currentChallenge) {
           case LivenessChallenge.turnLeft:
             if (mounted) setState(() => _realtimeWarning = "Quay nhẹ đầu sang TRÁI");
             if (rotY < -15) _livenessState = LivenessState.returnFrontal;
             break;
           case LivenessChallenge.turnRight:
             if (mounted) setState(() => _realtimeWarning = "Quay nhẹ đầu sang PHẢI");
             if (rotY > 15) _livenessState = LivenessState.returnFrontal;
             break;
           case LivenessChallenge.smile:
             if (mounted) setState(() => _realtimeWarning = "Hãy MỈM CƯỜI");
             if (smiling > 0.7) _livenessState = LivenessState.returnFrontal;
             break;
           case LivenessChallenge.blink:
             if (mounted) setState(() => _realtimeWarning = "Hãy CHỚP MẮT");
             if (leftEyeOpen < 0.2 && rightEyeOpen < 0.2) _livenessState = LivenessState.returnFrontal;
             break;
         }
         _isProcessingFrame = false;
         return;
      }

      if (_livenessState == LivenessState.returnFrontal) {
         if (mounted) setState(() => _realtimeWarning = "Tuyệt vời! Hãy nhìn thẳng");
         if (rotY.abs() <= 10 && rotZ.abs() <= 10) {
            _livenessState = LivenessState.passed;
         } else {
            _isProcessingFrame = false;
            return;
         }
      }

      // Vượt qua Liveness -> Kích hoạt chụp
      if (_livenessState == LivenessState.passed) {
        if (mounted) setState(() {
          _realtimeWarning = "Đang xử lý...";
          _uploadProgress = 0.2;
        });
        
        await _controller!.stopImageStream();
        _captureAndDetectFace();
      }


    } catch (e) {
      // Ignored
    } finally {
      _isProcessingFrame = false;
    }
  }

  @override
  void dispose() {
    _faceDetector.close();
    _controller?.dispose();
    _scanLineController.dispose();
    _cornerPulseController.dispose();
    super.dispose();
  }

  Future<void> _captureAndDetectFace() async {
    if (_isScanning || _controller == null || !_controller!.value.isInitialized) return;

    try {
      setState(() {
        _isScanning = true;
        _resultSuccess = null;
        _uploadProgress = 0.4;
      });

      final imageFile = await _controller!.takePicture();
      setState(() => _uploadProgress = 0.5);

      // Chạy ML Kit 1 lần nữa trên ảnh đã chụp để lấy boundingBox chuẩn (do độ phân giải ảnh chụp có thể khác luồng preview)
      Rect? finalBoundingBox;
      try {
        final inputImage = InputImage.fromFilePath(imageFile.path);
        final faces = await _faceDetector.processImage(inputImage);
        if (faces.isNotEmpty) {
           finalBoundingBox = faces.first.boundingBox;
        }
      } catch(e) {
        debugPrint('Không thể detect face trên ảnh chụp: $e');
      }

      setState(() => _uploadProgress = 0.6);

      if (_isOffline) {
        await _handleOfflineScan(imageFile);
      } else {
        await _recognizeViaApi(imageFile, finalBoundingBox);
      }
    } catch (e) {
      debugPrint('Lỗi camera/ML: $e');
    } finally {
      if (mounted) {
        setState(() {
          _isScanning = false;
          _resetLiveness(); // Reset trạng thái liveness cho lần quét sau
          _uploadProgress = 0.0;
        });
        
        // Khởi động lại stream nếu auto scan đang bật
        if (_autoScan) {
          try {
            final frontCamera = _cameras!.firstWhere(
              (c) => c.lensDirection == CameraLensDirection.front,
              orElse: () => _cameras![0],
            );
            _controller!.startImageStream((CameraImage image) {
              if (_autoScan && !_isScanning && mounted) {
                _processCameraImage(image, frontCamera);
              }
            });
          } catch(e) {}
        }
      }
    }
  }

  Future<void> _checkConnectivity() async {
    try {
      final result = await Connectivity().checkConnectivity();
      if (mounted) setState(() => _isOffline = result.contains(ConnectivityResult.none));
    } catch (_) {
      if (mounted) setState(() => _isOffline = true);
    }

    Connectivity().onConnectivityChanged.listen((result) {
      if (mounted) setState(() => _isOffline = result.contains(ConnectivityResult.none));
    });
  }

  Future<void> _handleOfflineScan(XFile image) async {
    try {
      await AttendanceRepository().saveAttendanceOffline('OFFLINE_PENDING', 0.0);
      if (!mounted) return;
      setState(() {
        _resultSuccess = true;
        _resultName = 'Ghi nhận Offline';
        _resultMssv = null;
        _resultMessage = 'Đã lưu cục bộ. Sẽ đồng bộ khi có mạng.';
        _autoScan = false;
      });
      Future.delayed(const Duration(seconds: 3), () {
        if (mounted) setState(() => _autoScan = true);
      });
    } catch (e) {
      if (mounted) {
        setState(() { _resultSuccess = false; _resultMessage = 'Lỗi lưu offline: $e'; });
        Future.delayed(const Duration(seconds: 2), () {
          if (mounted) setState(() { _resultSuccess = null; _resultMessage = null; });
        });
      }
    }
  }

  Future<Position?> _getCurrentLocation() async {
    bool serviceEnabled;
    LocationPermission permission;

    serviceEnabled = await Geolocator.isLocationServiceEnabled();
    if (!serviceEnabled) {
      return null;
    }

    permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
      if (permission == LocationPermission.denied) {
        return null;
      }
    }

    if (permission == LocationPermission.deniedForever) {
      return null;
    }

    return await Geolocator.getCurrentPosition(
      locationSettings: const LocationSettings(accuracy: LocationAccuracy.high, timeLimit: Duration(seconds: 10)),
    );
  }

  Future<void> _recognizeViaApi(XFile image, Rect? boundingBox) async {
    try {
      double? lat;
      double? lng;

      File fileToUpload = File(image.path);
      
      // Giai đoạn 1: Crop khuôn mặt nếu có bounding box để giảm tải dung lượng API
      if (boundingBox != null) {
         final croppedFile = await CameraUtils.cropFaceFromImage(fileToUpload, boundingBox);
         if (croppedFile != null) {
           fileToUpload = croppedFile;
           debugPrint('Đã crop ảnh khuôn mặt thành công');
         }
      }

      final bytes = await fileToUpload.readAsBytes();
      final base64Image = base64Encode(bytes);
      final dataUrl = "data:image/jpeg;base64,$base64Image";

      final result = await _apiService.recognizeFace(dataUrl, lat: lat, lng: lng);
      if (!mounted) return;

      if (result['success'] == true) {
        final student = result['student'];
        final att = result['attendance'];
        
        setState(() {
          _resultSuccess = true;
          _resultName = student['ho_ten'] ?? 'N/A';
          _resultMssv = student['mssv'] ?? '';
          _resultMessage = att != null ? (att['msg'] ?? 'Điểm danh thành công') : 'Nhận diện thành công';
          _autoScan = false;
        });

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
        setState(() { _resultSuccess = false; _resultMessage = 'Lỗi nhận diện: $e'; });
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
                  color: AppTheme.background,
                  child: const Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        CircularProgressIndicator(color: AppTheme.secondary),
                        SizedBox(height: 16),
                        Text("Khởi tạo hệ thống...", style: TextStyle(color: AppTheme.textSecondary)),
                      ],
                    ),
                  ),
                ),

          // Lớp phủ tối mờ
          Positioned.fill(child: Container(color: Colors.black.withValues(alpha: 0.4))),

          // ====== HUD SCANNER (KHUNG QUÉT) ======
          Center(
            child: AnimatedBuilder(
              animation: _cornerPulseAnimation,
              builder: (context, child) {
                return CustomPaint(
                  size: const Size(280, 350),
                  painter: HudScanFramePainter(
                    pulseValue: _cornerPulseAnimation.value,
                    isScanning: _isScanning,
                    isSuccess: _resultSuccess,
                  ),
                );
              },
            ),
          ).animate().fadeIn(duration: 800.ms),

          // Đường quét laser HUD
          if (_autoScan || _isScanning)
            Center(
              child: SizedBox(
                width: 280,
                height: 350,
                child: AnimatedBuilder(
                  animation: _scanLineAnimation,
                  builder: (context, child) {
                    return CustomPaint(
                      painter: HudScanLinePainter(progress: _scanLineAnimation.value),
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
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                child: Row(
                  children: [
                    _buildHudButton(
                      child: const Icon(Icons.arrow_back_ios_new, color: AppTheme.textPrimary, size: 18),
                      onTap: () => Navigator.pop(context),
                    ),
                    const Spacer(),
                    // Trạng thái Online/Offline
                    _buildHudContainer(
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Container(
                            width: 8, height: 8,
                            decoration: BoxDecoration(
                              color: _isOffline ? AppTheme.error : AppTheme.success,
                              shape: BoxShape.circle,
                              boxShadow: [BoxShadow(color: (_isOffline ? AppTheme.error : AppTheme.success).withValues(alpha: 0.6), blurRadius: 8)],
                            ),
                          ),
                          const SizedBox(width: 8),
                          Text(
                            _isOffline ? 'OFFLINE' : 'ONLINE',
                            style: const TextStyle(color: AppTheme.textPrimary, fontSize: 10, fontWeight: FontWeight.w900, letterSpacing: 1),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(width: 12),
                    // Nút On/Off AI
                    _buildHudButton(
                      child: Icon(
                        _autoScan ? Icons.smart_toy : Icons.pause,
                        color: _autoScan ? AppTheme.secondary : AppTheme.textSecondary,
                        size: 20,
                      ),
                      onTap: () => setState(() => _autoScan = !_autoScan),
                    ),
                  ],
                ),
              ),
            ),
          ).animate().fadeIn().slideY(begin: -0.5, end: 0),

          // ====== TRẠNG THÁI STATUS (DƯỚI HUD) ======
          Positioned(
            bottom: 120,
            left: 0,
            right: 0,
            child: Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  _buildHudContainer(
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        if (_isScanning)
                          const SizedBox(
                            width: 14, height: 14,
                            child: CircularProgressIndicator(color: AppTheme.secondary, strokeWidth: 2),
                          )
                        else
                          Icon(
                            _autoScan ? Icons.radar : Icons.motion_photos_paused, 
                            color: _autoScan ? AppTheme.secondary : AppTheme.textMuted, 
                            size: 16
                          ),
                        const SizedBox(width: 10),
                        Text(
                          _isScanning ? "ĐANG TẢI LÊN..." : _autoScan ? _realtimeWarning.toUpperCase() : "TẠM DỪNG",
                          style: TextStyle(
                            color: _isScanning ? AppTheme.secondary : AppTheme.textPrimary, 
                            fontSize: 12, 
                            fontWeight: FontWeight.w900, 
                            letterSpacing: 2
                          ),
                        ),
                      ],
                    ),
                  ).animate(target: _isScanning ? 1 : 0).shimmer(duration: 1.seconds),
                  
                  // Progress Bar cho quá trình upload/phân tích
                  if (_isScanning || _uploadProgress > 0)
                    Container(
                      width: 200,
                      height: 4,
                      margin: const EdgeInsets.only(top: 16),
                      decoration: BoxDecoration(
                        color: Colors.white.withValues(alpha: 0.2),
                        borderRadius: BorderRadius.circular(2),
                      ),
                      child: FractionallySizedBox(
                        alignment: Alignment.centerLeft,
                        widthFactor: _uploadProgress > 0 ? _uploadProgress : null,
                        child: Container(
                          decoration: BoxDecoration(
                            color: AppTheme.secondary,
                            borderRadius: BorderRadius.circular(2),
                            boxShadow: [
                              BoxShadow(color: AppTheme.secondary.withValues(alpha: 0.6), blurRadius: 4)
                            ]
                          ),
                        ),
                      ),
                    ),
                ],
              ),
            ),
          ),

          // ====== KẾT QUẢ HIỂN THỊ (GLASSMORPHISM) ======
          if (_resultSuccess != null)
            Positioned(
              bottom: 40,
              left: 20,
              right: 20,
              child: Container(
                padding: const EdgeInsets.all(20),
                decoration: AppTheme.modernCardDecoration(
                  color: (_resultSuccess == true ? AppTheme.success : AppTheme.error).withOpacity(0.15),
                  borderRadius: 24,
                ).copyWith(
                  border: Border.all(
                    color: (_resultSuccess == true ? AppTheme.success : AppTheme.error).withOpacity(0.5),
                  ),
                ),
                child: Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: Colors.white.withValues(alpha: 0.2),
                        shape: BoxShape.circle,
                      ),
                      child: Icon(
                        _resultSuccess == true ? Icons.check_circle : Icons.error_outline,
                        color: AppTheme.textPrimary,
                        size: 28,
                      ),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          if (_resultName != null)
                            Text(_resultName!, style: const TextStyle(color: AppTheme.textPrimary, fontSize: 18, fontWeight: FontWeight.bold)),
                          if (_resultMssv != null)
                            Text("MSSV: $_resultMssv", style: const TextStyle(color: AppTheme.textSecondary, fontSize: 12)),
                          if (_resultMessage != null)
                            Padding(
                              padding: const EdgeInsets.only(top: 4),
                              child: Text(_resultMessage!, style: const TextStyle(color: AppTheme.textPrimary, fontSize: 13, fontWeight: FontWeight.w500)),
                            ),
                        ],
                      ),
                    ),
                  ],
                ),
              ).animate().fadeIn().slideY(begin: 0.5, end: 0),
            )
          else
            // Nút chụp thủ công ở dưới cùng
            Positioned(
               bottom: 40,
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
                       border: Border.all(color: Colors.white.withValues(alpha: 0.5), width: 2),
                     ),
                     child: Container(
                       margin: const EdgeInsets.all(4),
                       decoration: BoxDecoration(
                         shape: BoxShape.circle, 
                         color: AppTheme.secondary.withValues(alpha: 0.8),
                         boxShadow: [BoxShadow(color: AppTheme.secondary.withValues(alpha: 0.5), blurRadius: 10)]
                       ),
                       child: const Icon(Icons.camera, color: Colors.white, size: 28),
                     ),
                   ),
                 ),
               ),
            ),
        ],
      ),
    );
  }

  Widget _buildHudButton({required Widget child, required VoidCallback onTap}) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: AppTheme.modernCardDecoration(color: AppTheme.surfaceLight.withOpacity(0.8), borderRadius: 16),
        child: child,
      ),
    );
  }

  Widget _buildHudContainer({required Widget child}) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: AppTheme.modernCardDecoration(color: AppTheme.surfaceLight.withOpacity(0.8), borderRadius: 16),
      child: child,
    );
  }
}

class HudScanFramePainter extends CustomPainter {
  final double pulseValue;
  final bool isScanning;
  final bool? isSuccess;

  HudScanFramePainter({required this.pulseValue, required this.isScanning, this.isSuccess});

  @override
  void paint(Canvas canvas, Size size) {
    Color frameColor;
    if (isSuccess == true) {
      frameColor = AppTheme.success;
    } else if (isSuccess == false) frameColor = AppTheme.error;
    else if (isScanning) frameColor = AppTheme.primary;
    else frameColor = AppTheme.secondary;

    final cornerLength = size.width * 0.2;
    const radius = 40.0; // Góc bo tròn lớn hơn (Modern style)

    final paint = Paint()
      ..color = frameColor.withValues(alpha: pulseValue)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 4.0
      ..strokeCap = StrokeCap.round;

    final glowPaint = Paint()
      ..color = frameColor.withValues(alpha: 0.3 * pulseValue)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 12.0
      ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 12);

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
  bool shouldRepaint(covariant HudScanFramePainter old) =>
      old.pulseValue != pulseValue || old.isScanning != isScanning || old.isSuccess != isSuccess;
}

class HudScanLinePainter extends CustomPainter {
  final double progress;
  HudScanLinePainter({required this.progress});

  @override
  void paint(Canvas canvas, Size size) {
    final y = size.height * progress;
    const color = AppTheme.secondary;

    // Đường tia laser
    canvas.drawRect(
      Rect.fromLTWH(0, y - 1, size.width, 2),
      Paint()
        ..shader = const LinearGradient(
          colors: [Colors.transparent, color, Colors.transparent],
          stops: [0.0, 0.5, 1.0],
        ).createShader(Rect.fromLTWH(0, y - 1, size.width, 2)),
    );

    // Vệt sáng (Glow trail)
    canvas.drawRect(
      Rect.fromLTWH(0, max(0, y - 60), size.width, 60),
      Paint()
        ..shader = LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [Colors.transparent, color.withValues(alpha: 0.2)],
        ).createShader(Rect.fromLTWH(0, max(0, y - 60), size.width, 60)),
    );
  }

  @override
  bool shouldRepaint(covariant HudScanLinePainter old) => old.progress != progress;
}
