import 'dart:async';
import 'package:flutter/material.dart';
import 'package:qr_flutter/qr_flutter.dart';
import 'package:geolocator/geolocator.dart';
import '../models/session_model.dart';
import '../services/api_service.dart';
import 'admin_session_detail_screen.dart';

/// Màn hình Admin tạo & quản lý phiên điểm danh
class AdminSessionScreen extends StatefulWidget {
  const AdminSessionScreen({super.key});
  @override
  State<AdminSessionScreen> createState() => _AdminSessionScreenState();
}

class _AdminSessionScreenState extends State<AdminSessionScreen> {
  final ApiService _api = ApiService();
  List<AttendanceSession> _sessions = [];
  List<dynamic> _classes = [];
  bool _isLoading = true;
  Timer? _refreshTimer;

  @override
  void initState() {
    super.initState();
    _loadData();
    _refreshTimer = Timer.periodic(const Duration(seconds: 10), (_) => _loadSessions());
  }

  @override
  void dispose() {
    _refreshTimer?.cancel();
    super.dispose();
  }

  Future<void> _loadData() async {
    await Future.wait([_loadSessions(), _loadClasses()]);
  }

  Future<void> _loadSessions() async {
    try {
      final result = await _api.getActiveSessions();
      if (!mounted) return;
      if (result['success'] == true) {
        setState(() {
          _sessions = (result['data'] as List).map((e) => AttendanceSession.fromJson(e)).toList();
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _loadClasses() async {
    try {
      _classes = await _api.getClasses();
    } catch (_) {}
  }

  void _showCreateDialog() {
    if (_classes.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: const Text('Không có lớp học nào!'), backgroundColor: Colors.orange,
          behavior: SnackBarBehavior.floating, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10))),
      );
      return;
    }

    int? selectedLopId;
    int duration = 90;
    final moTaController = TextEditingController();

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setModalState) => Container(
          padding: EdgeInsets.only(bottom: MediaQuery.of(ctx).viewInsets.bottom),
          decoration: const BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
          ),
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
              // Handle bar
              Center(child: Container(width: 40, height: 4, decoration: BoxDecoration(
                color: Colors.grey[300], borderRadius: BorderRadius.circular(2)))),
              const SizedBox(height: 20),

              // Title
              const Row(children: [
                Icon(Icons.add_circle, color: Color(0xFF10B981), size: 28),
                SizedBox(width: 10),
                Text('Mở Phiên Điểm Danh', style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Color(0xFF1B3A5C))),
              ]),
              const SizedBox(height: 24),

              // Chọn lớp
              const Text('Chọn lớp *', style: TextStyle(fontWeight: FontWeight.w600, color: Color(0xFF1B3A5C), fontSize: 14)),
              const SizedBox(height: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 14),
                decoration: BoxDecoration(
                  color: Colors.grey[50], borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: Colors.grey[200]!),
                ),
                child: DropdownButtonHideUnderline(
                  child: DropdownButton<int>(
                    isExpanded: true,
                    value: selectedLopId,
                    hint: const Text('-- Chọn lớp học --'),
                    items: _classes.map<DropdownMenuItem<int>>((c) => DropdownMenuItem(
                      value: c['id'],
                      child: Text('${c['ma_lop']} - ${c['ten_lop']}', overflow: TextOverflow.ellipsis),
                    )).toList(),
                    onChanged: (v) => setModalState(() => selectedLopId = v),
                  ),
                ),
              ),
              const SizedBox(height: 18),

              // Thời lượng
              const Text('Thời lượng (phút)', style: TextStyle(fontWeight: FontWeight.w600, color: Color(0xFF1B3A5C), fontSize: 14)),
              const SizedBox(height: 8),
              Row(children: [
                for (final m in [30, 60, 90, 120])
                  Expanded(child: Padding(
                    padding: const EdgeInsets.only(right: 8),
                    child: GestureDetector(
                      onTap: () => setModalState(() => duration = m),
                      child: Container(
                        padding: const EdgeInsets.symmetric(vertical: 12),
                        decoration: BoxDecoration(
                          color: duration == m ? const Color(0xFF1B3A5C) : Colors.grey[100],
                          borderRadius: BorderRadius.circular(10),
                          border: Border.all(color: duration == m ? const Color(0xFF1B3A5C) : Colors.grey[300]!),
                        ),
                        child: Center(child: Text('$m\'', style: TextStyle(
                          color: duration == m ? Colors.white : const Color(0xFF1B3A5C),
                          fontWeight: FontWeight.bold, fontSize: 15,
                        ))),
                      ),
                    ),
                  )),
              ]),
              const SizedBox(height: 18),

              // Ghi chú
              const Text('Ghi chú (tùy chọn)', style: TextStyle(fontWeight: FontWeight.w600, color: Color(0xFF1B3A5C), fontSize: 14)),
              const SizedBox(height: 8),
              TextField(
                controller: moTaController,
                decoration: InputDecoration(
                  hintText: 'VD: Buổi học thứ 5...',
                  filled: true, fillColor: Colors.grey[50],
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(14), borderSide: BorderSide(color: Colors.grey[200]!)),
                  enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(14), borderSide: BorderSide(color: Colors.grey[200]!)),
                  focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(14), borderSide: const BorderSide(color: Color(0xFF2E96EB))),
                ),
              ),
              const SizedBox(height: 24),

              // Nút tạo
              SizedBox(width: double.infinity, height: 52, child: ElevatedButton(
                onPressed: selectedLopId == null ? null : () => _createSession(ctx, selectedLopId!, duration, moTaController.text),
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF10B981), foregroundColor: Colors.white,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                  elevation: 2,
                ),
                child: const Row(mainAxisAlignment: MainAxisAlignment.center, children: [
                  Icon(Icons.play_circle_fill, size: 22),
                  SizedBox(width: 8),
                  Text('MỞ PHIÊN ĐIỂM DANH', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15, letterSpacing: 0.5)),
                ]),
              )),
              const SizedBox(height: 12),
            ]),
          ),
        ),
      ),
    );
  }

  Future<void> _createSession(BuildContext ctx, int lopId, int duration, String moTa) async {
    Navigator.pop(ctx);
    setState(() => _isLoading = true);
    
    double? lat;
    double? lng;

    try {
      // Lấy vị trí hiện tại của Admin (để làm mốc Geofencing)
      bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
      LocationPermission permission = await Geolocator.checkPermission();
      
      if (serviceEnabled && (permission == LocationPermission.always || permission == LocationPermission.whileInUse)) {
        Position position = await Geolocator.getCurrentPosition(desiredAccuracy: LocationAccuracy.high);
        lat = position.latitude;
        lng = position.longitude;
      } else if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
        if (permission == LocationPermission.always || permission == LocationPermission.whileInUse) {
           Position position = await Geolocator.getCurrentPosition(desiredAccuracy: LocationAccuracy.high);
           lat = position.latitude;
           lng = position.longitude;
        }
      }
    } catch (e) {
      debugPrint("Lỗi lấy vị trí Admin: $e");
    }

    try {
      final result = await _api.createSession(lopId, durationMinutes: duration, moTa: moTa, lat: lat, lng: lng);
      if (mounted) {
        final success = result['success'] == true;
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text(result['message'] ?? (success ? 'Thành công' : 'Thất bại')),
          backgroundColor: success ? const Color(0xFF10B981) : Colors.redAccent,
          behavior: SnackBarBehavior.floating,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
        ));
        _loadSessions();
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Lỗi: $e'), backgroundColor: Colors.redAccent));
        setState(() => _isLoading = false);
      }
    }
  }

  Future<void> _stopSession(int sessionId) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Text('Đóng phiên?'),
        content: const Text('Sinh viên sẽ không thể điểm danh phiên này nữa.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Hủy')),
          ElevatedButton(
            onPressed: () => Navigator.pop(ctx, true),
            style: ElevatedButton.styleFrom(backgroundColor: Colors.redAccent),
            child: const Text('Đóng phiên', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );
    if (confirm != true) return;

    try {
      final result = await _api.stopSession(sessionId);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text(result['message'] ?? 'Đã đóng phiên'),
          backgroundColor: const Color(0xFF10B981),
          behavior: SnackBarBehavior.floating,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
        ));
        _loadSessions();
      }
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Lỗi: $e')));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF0F4F8),
      appBar: AppBar(
        title: const Text('Quản Lý Phiên Điểm Danh', style: TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: const Color(0xFF1B3A5C),
        foregroundColor: Colors.white,
        elevation: 0,
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _showCreateDialog,
        backgroundColor: const Color(0xFF10B981),
        icon: const Icon(Icons.add),
        label: const Text('Mở phiên mới', style: TextStyle(fontWeight: FontWeight.bold)),
      ),
      body: _isLoading
        ? const Center(child: CircularProgressIndicator(color: Color(0xFF1B3A5C)))
        : RefreshIndicator(
            onRefresh: _loadSessions,
            child: _sessions.isEmpty
              ? ListView(children: [
                  SizedBox(height: MediaQuery.of(context).size.height * 0.25),
                  _buildEmptyState(),
                ])
              : ListView.builder(
                  padding: const EdgeInsets.fromLTRB(16, 16, 16, 80),
                  itemCount: _sessions.length + 1,
                  itemBuilder: (ctx, i) {
                    if (i == 0) return _buildStatsHeader();
                    return _buildSessionCard(_sessions[i - 1]);
                  },
                ),
          ),
    );
  }

  Widget _buildStatsHeader() {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        gradient: const LinearGradient(colors: [Color(0xFF1B3A5C), Color(0xFF2A5298)]),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Row(children: [
        Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(color: Colors.white.withOpacity(0.15), borderRadius: BorderRadius.circular(12)),
          child: const Icon(Icons.event_available, color: Colors.white, size: 28),
        ),
        const SizedBox(width: 14),
        Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text('${_sessions.length} phiên đang mở', style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
          Text('Sinh viên có thể điểm danh ngay', style: TextStyle(color: Colors.white.withOpacity(0.7), fontSize: 13)),
        ])),
      ]),
    );
  }

  Widget _buildSessionCard(AttendanceSession session) {
    final remaining = session.thoiGianConLai;
    final remainingStr = remaining != null ? '${remaining.inMinutes} phút' : '∞';

    return GestureDetector(
      onTap: () {
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (_) => AdminSessionDetailScreen(
              sessionId: session.id,
              tenLop: session.tenLop,
            ),
          ),
        );
      },
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.all(18),
        decoration: BoxDecoration(
          color: Colors.white, borderRadius: BorderRadius.circular(16),
          boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.04), blurRadius: 10, offset: const Offset(0, 4))],
        ),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(color: const Color(0xFF10B981).withOpacity(0.1), borderRadius: BorderRadius.circular(12)),
            child: const Icon(Icons.class_, color: Color(0xFF10B981), size: 24),
          ),
          const SizedBox(width: 14),
          Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(session.tenLop, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: Color(0xFF1B3A5C))),
            const SizedBox(height: 2),
            Text(session.maLop, style: TextStyle(color: const Color(0xFF1B3A5C).withOpacity(0.5), fontSize: 13)),
          ])),
          // Các nút hành động
          Row(children: [
            GestureDetector(
              onTap: () {
                showDialog(
                  context: context,
                  builder: (context) => AlertDialog(
                    title: const Text('Mã QR Điểm Danh', textAlign: TextAlign.center),
                    content: SizedBox(
                      width: 250,
                      height: 250,
                      child: Center(
                        child: QrImageView(
                          data: 'MTUFACE_SESSION_${session.id}',
                          version: QrVersions.auto,
                          size: 200.0,
                        ),
                      ),
                    ),
                    actions: [
                      TextButton(onPressed: () => Navigator.pop(context), child: const Text('Đóng'))
                    ],
                  ),
                );
              },
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                decoration: BoxDecoration(color: Colors.blueAccent.withOpacity(0.1), borderRadius: BorderRadius.circular(10)),
                child: const Row(mainAxisSize: MainAxisSize.min, children: [
                  Icon(Icons.qr_code, color: Colors.blueAccent, size: 16),
                  SizedBox(width: 4),
                  Text('Mã QR', style: TextStyle(color: Colors.blueAccent, fontWeight: FontWeight.bold, fontSize: 12)),
                ]),
              ),
            ),
            const SizedBox(width: 8),
            // Nút đóng phiên
            GestureDetector(
              onTap: () => _stopSession(session.id),
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                decoration: BoxDecoration(color: Colors.redAccent.withOpacity(0.1), borderRadius: BorderRadius.circular(10)),
                child: const Row(mainAxisSize: MainAxisSize.min, children: [
                  Icon(Icons.stop_circle, color: Colors.redAccent, size: 16),
                  SizedBox(width: 4),
                  Text('Đóng', style: TextStyle(color: Colors.redAccent, fontWeight: FontWeight.bold, fontSize: 12)),
                ]),
              ),
            ),
          ]),
        ]),
        const SizedBox(height: 14),
        // Info row
        Row(children: [
          _chip(Icons.people, '${session.soDaDiemDanh} đã ĐD', const Color(0xFF10B981)),
          const SizedBox(width: 8),
          _chip(Icons.timer, 'Còn $remainingStr', const Color(0xFF2E96EB)),
          if (session.giaoVien != null && session.giaoVien!.isNotEmpty) ...[
            const SizedBox(width: 8),
            _chip(Icons.person, session.giaoVien!, const Color(0xFF6366F1)),
          ],
        ]),
        if (session.moTa != null && session.moTa!.isNotEmpty) ...[
          const SizedBox(height: 10),
          Text(session.moTa!, style: TextStyle(color: const Color(0xFF1B3A5C).withOpacity(0.5), fontSize: 12, fontStyle: FontStyle.italic)),
        ],
      ]),
      ),
    );
  }

  Widget _chip(IconData icon, String text, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(color: color.withOpacity(0.08), borderRadius: BorderRadius.circular(8)),
      child: Row(mainAxisSize: MainAxisSize.min, children: [
        Icon(icon, size: 12, color: color),
        const SizedBox(width: 4),
        Text(text, style: TextStyle(fontSize: 11, color: color, fontWeight: FontWeight.w600)),
      ]),
    );
  }

  Widget _buildEmptyState() {
    return Column(mainAxisSize: MainAxisSize.min, children: [
      Container(
        padding: const EdgeInsets.all(24),
        decoration: BoxDecoration(color: const Color(0xFF1B3A5C).withOpacity(0.06), shape: BoxShape.circle),
        child: const Icon(Icons.event_busy, color: Color(0xFF1B3A5C), size: 48),
      ),
      const SizedBox(height: 20),
      const Text('Chưa có phiên nào đang mở', style: TextStyle(fontSize: 17, fontWeight: FontWeight.bold, color: Color(0xFF1B3A5C))),
      const SizedBox(height: 8),
      Text('Nhấn nút bên dưới để mở phiên điểm danh', style: TextStyle(color: const Color(0xFF1B3A5C).withOpacity(0.5))),
    ]);
  }
}
