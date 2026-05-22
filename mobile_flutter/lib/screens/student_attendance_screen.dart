import 'dart:async';
import 'dart:convert';
import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import 'package:geolocator/geolocator.dart';
import '../models/session_model.dart';
import '../services/api_service.dart';
import 'package:provider/provider.dart';
import '../providers/attendance_provider.dart';

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
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        title: const Text('Điểm Danh', style: TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: const Color(0xFF1E293B),
        foregroundColor: Colors.white,
        elevation: 0,
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: () { setState(() => _isLoading = true); _loadSessions(); }),
        ],
      ),
      body: _isLoading
        ? const Center(child: CircularProgressIndicator(color: Color(0xFF1E293B)))
        : _errorMessage != null
          ? Center(child: Column(mainAxisSize: MainAxisSize.min, children: [
              const Icon(Icons.wifi_off, size: 48, color: Colors.grey),
              const SizedBox(height: 12),
              Text(_errorMessage!, style: const TextStyle(color: Colors.grey)),
              const SizedBox(height: 12),
              ElevatedButton(onPressed: _loadSessions, child: const Text('Thử lại')),
            ]))
          : _sessions.isEmpty
            ? _buildEmptyState()
            : RefreshIndicator(
                onRefresh: _loadSessions,
                child: ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: _sessions.length + 1,
                  itemBuilder: (ctx, i) {
                    if (i == 0) return _buildHeader();
                    return _buildSessionCard(_sessions[i - 1]);
                  },
                ),
              ),
    );
  }

  Widget _buildHeader() {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Container(
        padding: const EdgeInsets.all(18),
        decoration: BoxDecoration(
          gradient: const LinearGradient(colors: [Color(0xFF4F46E5), Color(0xFF7C3AED)]),
          borderRadius: BorderRadius.circular(16),
        ),
        child: Row(children: [
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(color: Colors.white.withOpacity(0.15), borderRadius: BorderRadius.circular(12)),
            child: const Icon(Icons.qr_code_scanner, color: Colors.white, size: 28),
          ),
          const SizedBox(width: 14),
          Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            const Text('Phiên Điểm Danh', style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
            Text('Chọn lớp đang mở để quét khuôn mặt', style: TextStyle(color: Colors.white.withOpacity(0.7), fontSize: 13)),
          ])),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
            decoration: BoxDecoration(color: const Color(0xFF10B981).withOpacity(0.2), borderRadius: BorderRadius.circular(20)),
            child: Text('${_sessions.length}', style: const TextStyle(color: Color(0xFF10B981), fontWeight: FontWeight.bold, fontSize: 16)),
          ),
        ]),
      ),
    );
  }

  Widget _buildSessionCard(AttendanceSession session) {
    final remaining = session.thoiGianConLai;
    final remainingStr = remaining != null ? '${remaining.inMinutes} phút' : 'Không giới hạn';
    final isExpired = session.isExpired;

    return GestureDetector(
      onTap: isExpired ? null : () => _openScanForSession(session),
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.all(18),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
          border: session.daDiemDanhChua ? Border.all(color: const Color(0xFF10B981), width: 2) : null,
          boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.04), blurRadius: 10, offset: const Offset(0, 4))],
        ),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: (session.daDiemDanhChua ? const Color(0xFF10B981) : const Color(0xFF2E96EB)).withOpacity(0.1),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Icon(
                session.daDiemDanhChua ? Icons.check_circle : Icons.class_,
                color: session.daDiemDanhChua ? const Color(0xFF10B981) : const Color(0xFF2E96EB), size: 24,
              ),
            ),
            const SizedBox(width: 14),
            Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(session.tenLop, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: Color(0xFF1E293B))),
              const SizedBox(height: 4),
              Text(session.maLop, style: TextStyle(color: const Color(0xFF1E293B).withOpacity(0.5), fontSize: 13)),
            ])),
            if (session.daDiemDanhChua)
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                decoration: BoxDecoration(color: const Color(0xFF10B981).withOpacity(0.1), borderRadius: BorderRadius.circular(20)),
                child: const Text('Đã điểm danh ✓', style: TextStyle(color: Color(0xFF10B981), fontWeight: FontWeight.bold, fontSize: 11)),
              )
            else
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(color: const Color(0xFF2E96EB).withOpacity(0.1), borderRadius: BorderRadius.circular(10)),
                child: const Icon(Icons.arrow_forward_ios, color: Color(0xFF2E96EB), size: 16),
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
    );
  }

  Widget _infoChip(IconData icon, String text) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(color: const Color(0xFF1E293B).withOpacity(0.05), borderRadius: BorderRadius.circular(8)),
      child: Row(mainAxisSize: MainAxisSize.min, children: [
        Icon(icon, size: 12, color: const Color(0xFF1E293B).withOpacity(0.5)),
        const SizedBox(width: 4),
        Flexible(child: Text(text, style: TextStyle(fontSize: 11, color: const Color(0xFF1E293B).withOpacity(0.6)), overflow: TextOverflow.ellipsis)),
      ]),
    );
  }

  Widget _buildEmptyState() {
    return Center(child: Column(mainAxisSize: MainAxisSize.min, children: [
      Container(
        padding: const EdgeInsets.all(24),
        decoration: BoxDecoration(color: const Color(0xFF1E293B).withOpacity(0.06), shape: BoxShape.circle),
        child: const Icon(Icons.event_busy, color: Color(0xFF1E293B), size: 48),
      ),
      const SizedBox(height: 20),
      const Text('Không có phiên điểm danh', style: TextStyle(fontSize: 17, fontWeight: FontWeight.bold, color: Color(0xFF1E293B))),
      const SizedBox(height: 8),
      Text('Chờ Admin mở phiên điểm danh cho lớp bạn', style: TextStyle(color: const Color(0xFF1E293B).withOpacity(0.5), fontSize: 14)),
      const SizedBox(height: 24),
      ElevatedButton.icon(
        onPressed: () { setState(() => _isLoading = true); _loadSessions(); },
        icon: const Icon(Icons.refresh),
        label: const Text('Làm mới'),
        style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF1E293B), foregroundColor: Colors.white,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12))),
      ),
    ]));
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

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(vsync: this, duration: const Duration(milliseconds: 1500))..repeat(reverse: true);
    _initCamera();
  }

  Future<void> _initCamera() async {
    try {
      final cameras = await availableCameras();
      final front = cameras.firstWhere((c) => c.lensDirection == CameraLensDirection.front, orElse: () => cameras[0]);
      _controller = CameraController(front, ResolutionPreset.medium, enableAudio: false);
      await _controller!.initialize();
      if (mounted) setState(() => _isInitialized = true);
    } catch (e) {
      if (mounted) setState(() => _statusMessage = 'Không thể mở camera: $e');
    }
  }

  @override
  void dispose() {
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
      try {
        setState(() => _statusMessage = 'Đang kiểm tra quyền vị trí...');
        
        // Kiểm tra service và quyền GPS
        bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
        if (!serviceEnabled) {
          throw Exception('Vui lòng vuốt từ trên xuống và Bật GPS (Vị trí) trên điện thoại!');
        }

        LocationPermission permission = await Geolocator.checkPermission();
        if (permission == LocationPermission.denied) {
          permission = await Geolocator.requestPermission();
          if (permission == LocationPermission.denied) {
            throw Exception('Bạn cần cấp quyền vị trí để điểm danh');
          }
        }
        
        if (permission == LocationPermission.deniedForever) {
          throw Exception('Vui lòng vào Cài đặt máy để cấp quyền vị trí cho MTU Face');
        }

        setState(() => _statusMessage = 'Đang lấy vị trí GPS...');
        Position pos = await Geolocator.getCurrentPosition(desiredAccuracy: LocationAccuracy.high).timeout(const Duration(seconds: 7));
        lat = pos.latitude;
        lng = pos.longitude;
      } catch (e) {
        if (mounted) {
          setState(() { _success = false; _statusMessage = e.toString().replaceAll('Exception: ', ''); });
          await Future.delayed(const Duration(seconds: 3));
        }
        // Vẫn tiếp tục nếu Backend không yêu cầu GPS khắt khe, 
        // nhưng nếu Backend yêu cầu, backend sẽ tự trả về lỗi.
      }

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
      if (mounted) setState(() => _isProcessing = false);
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
          Container(color: const Color(0xFF0F172A), child: const Center(child: CircularProgressIndicator(color: Color(0xFF2E96EB)))),

        // Dark overlay
        Positioned.fill(child: Container(color: Colors.black.withOpacity(0.3))),

        // Top bar
        Positioned(top: 0, left: 0, right: 0, child: SafeArea(child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(children: [
            GestureDetector(
              onTap: () => Navigator.pop(context),
              child: ClipRRect(borderRadius: BorderRadius.circular(12), child: BackdropFilter(
                filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
                child: Container(padding: const EdgeInsets.all(10), decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.15), borderRadius: BorderRadius.circular(12)),
                  child: const Icon(Icons.arrow_back_ios_new, color: Colors.white, size: 18)),
              )),
            ),
            const SizedBox(width: 12),
            Expanded(child: ClipRRect(borderRadius: BorderRadius.circular(12), child: BackdropFilter(
              filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
              child: Container(padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                decoration: BoxDecoration(color: Colors.white.withOpacity(0.15), borderRadius: BorderRadius.circular(12)),
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text(widget.session.tenLop, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 14)),
                  Text(widget.session.maLop, style: TextStyle(color: Colors.white.withOpacity(0.7), fontSize: 11)),
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
                  color: (_success == true ? const Color(0xFF10B981) : _success == false ? Colors.redAccent : Colors.blueAccent).withOpacity(0.25),
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: (_success == true ? const Color(0xFF10B981) : _success == false ? Colors.redAccent : Colors.blueAccent).withOpacity(0.4)),
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
            Text('Đưa khuôn mặt vào khung hình và nhấn nút bên dưới',
              textAlign: TextAlign.center, style: TextStyle(color: Colors.white.withOpacity(0.8), fontSize: 14)),
            const SizedBox(height: 20),
            GestureDetector(
              onTap: _isProcessing ? null : _captureAndCheckin,
              child: AnimatedBuilder(animation: _pulseController, builder: (ctx, _) {
                return Container(
                  width: 72, height: 72,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    border: Border.all(color: Colors.white.withOpacity(0.5 + _pulseController.value * 0.5), width: 3),
                    boxShadow: [BoxShadow(color: const Color(0xFF2E96EB).withOpacity(0.3 * _pulseController.value), blurRadius: 20)],
                  ),
                  child: Container(
                    margin: const EdgeInsets.all(4),
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      gradient: LinearGradient(colors: [
                        _isProcessing ? Colors.orange : const Color(0xFF2E96EB),
                        _isProcessing ? Colors.deepOrange : const Color(0xFF1E293B),
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
