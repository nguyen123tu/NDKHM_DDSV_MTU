import 'dart:async';
import 'dart:convert';
import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import 'package:geolocator/geolocator.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../models/session_model.dart';
import '../services/api_service.dart';
import 'package:provider/provider.dart';
import '../providers/attendance_provider.dart';
import '../theme/app_theme.dart';
import '../widgets/neu_container.dart';
import '../widgets/neu_button.dart';
import 'dart:io';
import 'package:google_mlkit_face_detection/google_mlkit_face_detection.dart';
import '../utils/camera_utils.dart';

/// Màn hình điểm danh cho sinh viên
/// Flow: Xem phiên đang mở → Chọn phiên → Quét mặt → Server xác minh
class StudentAttendanceScreen extends StatefulWidget {
  const StudentAttendanceScreen({super.key});
  @override
  State<StudentAttendanceScreen> createState() => _StudentAttendanceScreenState();
}

class _StudentAttendanceScreenState extends State<StudentAttendanceScreen> {
  final ApiService _api = ApiService();
  List<AttendanceSession> _sessions = [];
  bool _isLoading = true;
  String? _errorMessage;
  Timer? _refreshTimer;

  @override
  void initState() {
    super.initState();
    _loadSessions();
    _refreshTimer = Timer.periodic(const Duration(seconds: 15), (_) => _loadSessions());
  }

  @override
  void dispose() {
    _refreshTimer?.cancel();
    super.dispose();
  }

  Future<void> _loadSessions() async {
    try {
      final result = await _api.getActiveSessions();
      if (!mounted) return;
      if (result['success'] == true) {
        final list = (result['data'] as List).map((e) => AttendanceSession.fromJson(e)).toList();
        setState(() { _sessions = list; _isLoading = false; _errorMessage = null; });
      } else {
        setState(() { _errorMessage = result['message']; _isLoading = false; });
      }
    } catch (e) {
      if (mounted) setState(() { _errorMessage = 'Lỗi kết nối: $e'; _isLoading = false; });
    }
  }

  void _openScanForSession(AttendanceSession session) {
    // Luôn cho mở camera - server sẽ xử lý nếu đã điểm danh rồi
    Navigator.push(context, MaterialPageRoute(
      builder: (_) => StudentFaceScanScreen(session: session),
    )).then((_) => _loadSessions());
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      appBar: AppBar(
        title: const Text('Điểm Danh', style: TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: Colors.transparent,
        foregroundColor: AppTheme.textPrimary,
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh, color: AppTheme.secondary),
            onPressed: () { setState(() => _isLoading = true); _loadSessions(); },
          ),
        ],
      ),
      body: Stack(
        children: [
          // Background - Deep Slate
          Container(color: AppTheme.background),

          // Glowing Orbs (Mesh Gradient Effect)
          Positioned(
            top: -100,
            right: -100,
            child: Container(
              width: 300,
              height: 300,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: AppTheme.primary.withOpacity(0.12),
              ),
            ),
          ).animate().fadeIn(duration: 1000.ms),

          _isLoading
            ? const Center(child: CircularProgressIndicator(color: AppTheme.secondary))
            : _errorMessage != null
              ? Center(child: Column(mainAxisSize: MainAxisSize.min, children: [
                  const Icon(Icons.wifi_off, size: 48, color: AppTheme.textMuted),
                  const SizedBox(height: 12),
                  Text(_errorMessage!, style: const TextStyle(color: AppTheme.textSecondary), textAlign: TextAlign.center),
                  const SizedBox(height: 16),
                  ElevatedButton.icon(
                    onPressed: _loadSessions,
                    icon: const Icon(Icons.refresh),
                    label: const Text('Thử lại'),
                  ),
                ]))
              : _sessions.isEmpty
                ? _buildEmptyState()
                : RefreshIndicator(
                    onRefresh: _loadSessions,
                    color: AppTheme.secondary,
                    backgroundColor: AppTheme.surface,
                    child: ListView.builder(
                      padding: const EdgeInsets.fromLTRB(16, 16, 16, 100), // Thêm padding 100px ở dưới đáy để không bị thanh Tab Bar lơ lửng che mất
                      itemCount: _sessions.length + 1,
                      itemBuilder: (ctx, i) {
                        if (i == 0) return _buildHeader();
                        return _buildSessionCard(_sessions[i - 1], i - 1);
                      },
                    ),
                  ),
        ],
      ),
    );
  }

  Widget _buildHeader() {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: NeuContainer(
        padding: const EdgeInsets.all(18),
        borderRadius: 20,
        child: Row(children: [
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              gradient: AppTheme.primaryGradient,
              borderRadius: BorderRadius.circular(12),
            ),
            child: const Icon(Icons.how_to_reg, color: Colors.white, size: 28),
          ),
          const SizedBox(width: 14),
          Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            const Text('Phiên Điểm Danh', style: TextStyle(color: AppTheme.textPrimary, fontSize: 18, fontWeight: FontWeight.bold)),
            const Text('Chọn lớp đang mở để quét khuôn mặt', style: TextStyle(color: AppTheme.textSecondary, fontSize: 13)),
          ])),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
            decoration: BoxDecoration(color: AppTheme.success.withValues(alpha: 0.25), borderRadius: BorderRadius.circular(20)),
            child: Text('${_sessions.length}', style: const TextStyle(color: AppTheme.success, fontWeight: FontWeight.bold, fontSize: 16)),
          ),
        ]),
      ),
    ).animate().fadeIn(duration: 400.ms).slideY(begin: -0.1, end: 0);
  }

  Widget _buildSessionCard(AttendanceSession session, int index) {
    final remaining = session.thoiGianConLai;
    final remainingStr = remaining != null ? '${remaining.inMinutes} phút' : 'Không giới hạn';
    final isExpired = session.isExpired;

    return GestureDetector(
      onTap: isExpired ? null : () => _openScanForSession(session),
      child: NeuContainer(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.all(18),
        borderRadius: 20,
        isPressed: session.daDiemDanhChua,
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: (session.daDiemDanhChua ? AppTheme.success : AppTheme.secondary).withValues(alpha: 0.15),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Icon(
                session.daDiemDanhChua ? Icons.check_circle : Icons.class_,
                color: session.daDiemDanhChua ? AppTheme.success : AppTheme.secondary, size: 24,
              ),
            ),
            const SizedBox(width: 14),
            Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(session.tenLop, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: AppTheme.textPrimary)),
              const SizedBox(height: 4),
              Text(session.maLop, style: const TextStyle(color: AppTheme.textMuted, fontSize: 13)),
            ])),
            if (session.daDiemDanhChua)
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                decoration: BoxDecoration(color: AppTheme.success.withValues(alpha: 0.15), borderRadius: BorderRadius.circular(20)),
                child: const Text('Đã điểm danh ✓', style: TextStyle(color: AppTheme.success, fontWeight: FontWeight.bold, fontSize: 11)),
              )
            else
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(color: AppTheme.secondary.withValues(alpha: 0.15), borderRadius: BorderRadius.circular(10)),
                child: const Icon(Icons.arrow_forward_ios, color: AppTheme.secondary, size: 16),
              ),
          ]),
          const SizedBox(height: 14),
          Row(children: [
            _infoChip(Icons.access_time, 'Còn $remainingStr'),
            const SizedBox(width: 10),
            _infoChip(Icons.people, '${session.soDaDiemDanh} đã điểm danh'),
            if (session.giaoVien != null && session.giaoVien!.isNotEmpty) ...[
              const SizedBox(width: 10),
              _infoChip(Icons.person, session.giaoVien!),
            ],
          ]),
        ]),
      ),
    ).animate().fadeIn(delay: Duration(milliseconds: 80 * index)).slideX(begin: 0.05, end: 0);
  }

  Widget _infoChip(IconData icon, String text) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(color: Colors.white.withValues(alpha: 0.06), borderRadius: BorderRadius.circular(8)),
      child: Row(mainAxisSize: MainAxisSize.min, children: [
        Icon(icon, size: 12, color: AppTheme.textMuted),
        const SizedBox(width: 4),
        Flexible(child: Text(text, style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary), overflow: TextOverflow.ellipsis)),
      ]),
    );
  }

  Widget _buildEmptyState() {
    return Center(child: Column(mainAxisSize: MainAxisSize.min, children: [
      NeuContainer(
        padding: const EdgeInsets.all(24),
        shape: BoxShape.circle,
        child: const Icon(Icons.event_busy, color: AppTheme.textSecondary, size: 48),
      ),
      const SizedBox(height: 20),
      const Text('Không có phiên điểm danh', style: TextStyle(fontSize: 17, fontWeight: FontWeight.bold, color: AppTheme.textPrimary)),
      const SizedBox(height: 8),
      const Text('Chờ Admin mở phiên điểm danh cho lớp bạn', style: TextStyle(color: AppTheme.textSecondary, fontSize: 14)),
      const SizedBox(height: 24),
      ElevatedButton.icon(
        onPressed: () { setState(() => _isLoading = true); _loadSessions(); },
        icon: const Icon(Icons.refresh),
        label: const Text('Làm mới'),
      ),
    ])).animate().fadeIn(duration: 400.ms).scale(begin: const Offset(0.9, 0.9));
  }
}

// =================================================================
// MÀN HÌNH QUÉT MẶT SINH VIÊN (Chỉ quét cho chính mình)
// =================================================================
class StudentFaceScanScreen extends StatefulWidget {
  final AttendanceSession session;
  const StudentFaceScanScreen({required this.session, super.key});
  @override
  State<StudentFaceScanScreen> createState() => _StudentFaceScanScreenState();
}

class _StudentFaceScanScreenState extends State<StudentFaceScanScreen> with TickerProviderStateMixin {
  CameraController? _controller;
  bool _isInitialized = false;
  bool _isProcessing = false;
  final ApiService _api = ApiService();

  late AnimationController _pulseController;
  String? _statusMessage;
  bool? _success;

  // Real-time Validation
  final FaceDetector _faceDetector = FaceDetector(
    options: FaceDetectorOptions(performanceMode: FaceDetectorMode.fast),
  );
  bool _isProcessingFrame = false;
  String _realtimeWarning = "Đang khởi tạo...";
  bool _hasBlinked = false;
  List<CameraDescription>? _cameras;

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(vsync: this, duration: const Duration(milliseconds: 1500))..repeat(reverse: true);
    _initCamera();
  }

  Future<void> _initCamera() async {
    try {
      _cameras = await availableCameras();
      if (_cameras == null || _cameras!.isEmpty) return;
      
      final front = _cameras!.firstWhere((c) => c.lensDirection == CameraLensDirection.front, orElse: () => _cameras![0]);
      _controller = CameraController(
        front, 
        ResolutionPreset.high, 
        enableAudio: false,
        imageFormatGroup: Platform.isAndroid ? ImageFormatGroup.yuv420 : ImageFormatGroup.bgra8888,
      );
      await _controller!.initialize();
      if (!mounted) return;
      
      await _controller!.setFocusMode(FocusMode.auto);
      await _controller!.setExposureMode(ExposureMode.auto);

      setState(() {
        _isInitialized = true;
        _realtimeWarning = "Vui lòng đưa khuôn mặt vào khung";
      });

      _controller!.startImageStream((CameraImage image) {
        if (!_isProcessing && mounted) {
          _processCameraImage(image, front);
        }
      });
    } catch (e) {
      if (mounted) setState(() => _statusMessage = 'Không thể mở camera: $e');
    }
  }

  Future<void> _processCameraImage(CameraImage image, CameraDescription camera) async {
    if (_isProcessingFrame || _isProcessing) return;
    _isProcessingFrame = true;

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

      final face = faces.first;
      
      final rotY = face.headEulerAngleY ?? 0;
      final rotZ = face.headEulerAngleZ ?? 0;
      if (rotY.abs() > 15 || rotZ.abs() > 15) {
        if (mounted) setState(() => _realtimeWarning = "Vui lòng nhìn thẳng camera");
        _isProcessingFrame = false;
        return;
      }

      final screenWidth = MediaQuery.of(context).size.width;
      if (face.boundingBox.width < screenWidth * 0.3) {
        if (mounted) setState(() => _realtimeWarning = "Hãy di chuyển lại gần hơn");
        _isProcessingFrame = false;
        return;
      }

      final leftEyeOpen = face.leftEyeOpenProbability ?? 1.0;
      final rightEyeOpen = face.rightEyeOpenProbability ?? 1.0;
      if (leftEyeOpen < 0.2 && rightEyeOpen < 0.2) {
        _hasBlinked = true;
      }

      if (!_hasBlinked) {
        if (mounted) setState(() => _realtimeWarning = "Vui lòng chớp mắt để xác thực");
        _isProcessingFrame = false;
        return;
      }

      if (mounted) setState(() {
        _realtimeWarning = "Hoàn hảo! Đang nhận diện...";
      });
      
      await _controller!.stopImageStream();
      _captureAndCheckin();

    } catch (e) {
      // Ignore
    } finally {
      _isProcessingFrame = false;
    }
  }

  @override
  void dispose() {
    _faceDetector.close();
    _controller?.dispose();
    _pulseController.dispose();
    super.dispose();
  }

  Future<void> _captureAndCheckin() async {
    if (_isProcessing || _controller == null || !_controller!.value.isInitialized) return;
    setState(() { _isProcessing = true; _statusMessage = 'Đang phân tích khuôn mặt...'; _success = null; });

    try {
      final image = await _controller!.takePicture();
      
      double? lat;
      double? lng;

      setState(() => _statusMessage = 'Đang gửi lên server xác minh...');
      final bytes = await image.readAsBytes();
      final b64 = "data:image/jpeg;base64,${base64Encode(bytes)}";
      final result = await _api.studentSelfCheckin(widget.session.id, b64, lat: lat, lng: lng);

      if (!mounted) return;
      if (result['success'] == true) {
        setState(() { _success = true; _statusMessage = result['message'] ?? 'Điểm danh thành công!'; });
        // Tự động làm mới lịch sử điểm danh ngoài màn hình chính
        try {
          Provider.of<AttendanceProvider>(context, listen: false).fetchDashboardData();
        } catch (_) {}
        Future.delayed(const Duration(seconds: 3), () { if (mounted) Navigator.pop(context); });
      } else {
        setState(() { _success = false; _statusMessage = result['message'] ?? 'Điểm danh thất bại'; });
        Future.delayed(const Duration(seconds: 3), () { if (mounted) setState(() { _statusMessage = null; _success = null; }); });
      }
    } catch (e) {
      if (mounted) {
        setState(() { _success = false; _statusMessage = 'Lỗi: $e'; });
        Future.delayed(const Duration(seconds: 2), () { if (mounted) setState(() { _statusMessage = null; _success = null; }); });
      }
    } finally {
      if (mounted) {
        setState(() {
          _isProcessing = false;
          _hasBlinked = false;
        });
        
        try {
          if (_cameras != null && _cameras!.isNotEmpty) {
            final front = _cameras!.firstWhere((c) => c.lensDirection == CameraLensDirection.front, orElse: () => _cameras![0]);
            _controller!.startImageStream((CameraImage image) {
              if (!_isProcessing && mounted) {
                _processCameraImage(image, front);
              }
            });
          }
        } catch (e) {}
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(children: [
        // Camera
        if (_isInitialized)
          SizedBox.expand(child: FittedBox(fit: BoxFit.cover, child: SizedBox(
            width: _controller!.value.previewSize?.height ?? 1,
            height: _controller!.value.previewSize?.width ?? 1,
            child: CameraPreview(_controller!),
          )))
        else
          Container(color: AppTheme.background, child: const Center(child: CircularProgressIndicator(color: AppTheme.secondary))),

        // Dark overlay
        Positioned.fill(child: Container(color: Colors.black.withValues(alpha: 0.3))),

        // Top bar
        Positioned(top: 0, left: 0, right: 0, child: SafeArea(child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(children: [
            GestureDetector(
              onTap: () => Navigator.pop(context),
              child: ClipRRect(borderRadius: BorderRadius.circular(12), child: BackdropFilter(
                filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
                child: Container(padding: const EdgeInsets.all(10), decoration: BoxDecoration(
                  color: Colors.white.withValues(alpha: 0.15), borderRadius: BorderRadius.circular(12)),
                  child: const Icon(Icons.arrow_back_ios_new, color: Colors.white, size: 18)),
              )),
            ),
            const SizedBox(width: 12),
            Expanded(child: ClipRRect(borderRadius: BorderRadius.circular(12), child: BackdropFilter(
              filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
              child: Container(padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                decoration: BoxDecoration(color: Colors.white.withValues(alpha: 0.15), borderRadius: BorderRadius.circular(12)),
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text(widget.session.tenLop, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 14)),
                  Text(widget.session.maLop, style: TextStyle(color: Colors.white.withValues(alpha: 0.7), fontSize: 11)),
                ]),
              ),
            ))),
          ]),
        ))),

        // Status message
        if (_statusMessage != null)
          Positioned(top: MediaQuery.of(context).padding.top + 80, left: 16, right: 16,
            child: ClipRRect(borderRadius: BorderRadius.circular(16), child: BackdropFilter(
              filter: ImageFilter.blur(sigmaX: 12, sigmaY: 12),
              child: Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: (_success == true ? const Color(0xFF10B981) : _success == false ? Colors.redAccent : Colors.blueAccent).withValues(alpha: 0.25),
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: (_success == true ? const Color(0xFF10B981) : _success == false ? Colors.redAccent : Colors.blueAccent).withValues(alpha: 0.4)),
                ),
                child: Row(children: [
                  Icon(_success == true ? Icons.check_circle : _success == false ? Icons.error : Icons.hourglass_empty,
                    color: Colors.white, size: 24),
                  const SizedBox(width: 12),
                  Expanded(child: Text(_statusMessage!, style: const TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.w500))),
                ]),
              ),
            )),
          ),

        // Instructions + capture button
        Positioned(bottom: 0, left: 0, right: 0, child: SafeArea(child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              decoration: BoxDecoration(
                color: _hasBlinked ? Colors.green.withValues(alpha: 0.8) : Colors.black.withValues(alpha: 0.6),
                borderRadius: BorderRadius.circular(20),
              ),
              child: Text(
                _isProcessing ? 'ĐANG TẢI LÊN...' : _realtimeWarning.toUpperCase(),
                textAlign: TextAlign.center, 
                style: const TextStyle(color: Colors.white, fontSize: 13, fontWeight: FontWeight.bold)
              ),
            ),
            const SizedBox(height: 20),
            GestureDetector(
              onTap: _isProcessing ? null : _captureAndCheckin,
              child: AnimatedBuilder(animation: _pulseController, builder: (ctx, _) {
                return Container(
                  width: 72, height: 72,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    border: Border.all(color: Colors.white.withValues(alpha: 0.5 + _pulseController.value * 0.5), width: 3),
                    boxShadow: [BoxShadow(color: AppTheme.primary.withOpacity(0.3 * _pulseController.value), blurRadius: 20)],
                  ),
                  child: Container(
                    margin: const EdgeInsets.all(4),
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      gradient: LinearGradient(colors: [
                        _isProcessing ? Colors.orange : AppTheme.primary,
                        _isProcessing ? Colors.deepOrange : AppTheme.secondary,
                      ]),
                    ),
                    child: Icon(_isProcessing ? Icons.hourglass_empty : Icons.face_retouching_natural,
                      color: Colors.white, size: 30),
                  ),
                );
              }),
            ),
          ]),
        ))),
      ]),
    );
  }
}
