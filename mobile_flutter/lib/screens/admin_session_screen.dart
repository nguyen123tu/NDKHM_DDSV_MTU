import 'dart:async';
import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:qr_flutter/qr_flutter.dart';
import 'package:geolocator/geolocator.dart';
import '../models/session_model.dart';
import '../services/api_service.dart';
import '../theme/app_theme.dart';
import 'admin_session_detail_screen.dart';
import '../widgets/neu_container.dart';
import '../widgets/neu_button.dart';

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
    _refreshTimer =
        Timer.periodic(const Duration(seconds: 10), (_) => _loadSessions());
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
          _sessions = (result['data'] as List)
              .map((e) => AttendanceSession.fromJson(e))
              .toList();
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

  // ====== TẠO PHIÊN ======
  void _showCreateDialog() {
    if (_classes.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content: const Text('Không có lớp học nào!'),
        backgroundColor: AppTheme.warning,
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      ));
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
        builder: (ctx, setModalState) => ClipRRect(
          borderRadius: const BorderRadius.vertical(top: Radius.circular(28)),
          child: BackdropFilter(
            filter: ImageFilter.blur(sigmaX: 20, sigmaY: 20),
            child: Container(
              padding:
                  EdgeInsets.only(bottom: MediaQuery.of(ctx).viewInsets.bottom),
              decoration: BoxDecoration(
                color: AppTheme.surface.withValues(alpha: 0.95),
                borderRadius:
                    const BorderRadius.vertical(top: Radius.circular(28)),
                border: Border(
                    top:
                        BorderSide(color: Colors.white.withValues(alpha: 0.1))),
              ),
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                    mainAxisSize: MainAxisSize.min,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Handle bar
                      Center(
                          child: Container(
                              width: 40,
                              height: 4,
                              decoration: BoxDecoration(
                                  color:
                                      AppTheme.textMuted.withValues(alpha: 0.3),
                                  borderRadius: BorderRadius.circular(2)))),
                      const SizedBox(height: 20),

                      // Title
                      Row(children: [
                        Container(
                          padding: const EdgeInsets.all(10),
                          decoration: BoxDecoration(
                            gradient: const LinearGradient(
                                colors: [AppTheme.success, Color(0xFF059669)]),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: const Icon(Icons.play_circle_fill,
                              color: Colors.white, size: 22),
                        ),
                        const SizedBox(width: 12),
                        const Text('Mở Phiên Điểm Danh',
                            style: TextStyle(
                                fontSize: 20,
                                fontWeight: FontWeight.bold,
                                color: AppTheme.textPrimary)),
                      ]),
                      const SizedBox(height: 24),

                      // Chọn lớp
                      const Text('Chọn lớp *',
                          style: TextStyle(
                              fontWeight: FontWeight.w600,
                              color: AppTheme.secondary,
                              fontSize: 13,
                              letterSpacing: 0.5)),
                      const SizedBox(height: 8),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 14),
                        decoration: AppTheme.modernCardDecoration(
                            borderRadius: 14,
                            color: AppTheme.surfaceLight.withOpacity(0.08)),
                        child: DropdownButtonHideUnderline(
                          child: DropdownButton<int>(
                            isExpanded: true,
                            value: selectedLopId,
                            dropdownColor: AppTheme.surface,
                            hint: Text('-- Chọn lớp học --',
                                style: TextStyle(
                                    color: AppTheme.textMuted
                                        .withValues(alpha: 0.5))),
                            iconEnabledColor: AppTheme.secondary,
                            style: const TextStyle(
                                color: AppTheme.textPrimary, fontSize: 14),
                            items: _classes
                                .map<DropdownMenuItem<int>>(
                                    (c) => DropdownMenuItem(
                                          value: c['id'],
                                          child: Text(
                                              '${c['ma_lop']} - ${c['ten_lop']}',
                                              overflow: TextOverflow.ellipsis),
                                        ))
                                .toList(),
                            onChanged: (v) =>
                                setModalState(() => selectedLopId = v),
                          ),
                        ),
                      ),
                      const SizedBox(height: 20),

                      // Thời lượng
                      const Text('Thời lượng',
                          style: TextStyle(
                              fontWeight: FontWeight.w600,
                              color: AppTheme.secondary,
                              fontSize: 13,
                              letterSpacing: 0.5)),
                      const SizedBox(height: 8),
                      Row(children: [
                        for (final m in [30, 60, 90, 120])
                          Expanded(
                              child: Padding(
                            padding: EdgeInsets.only(right: m == 120 ? 0 : 8),
                            child: GestureDetector(
                              onTap: () => setModalState(() => duration = m),
                              child: Container(
                                padding:
                                    const EdgeInsets.symmetric(vertical: 14),
                                decoration: duration == m
                                    ? BoxDecoration(
                                        gradient: const LinearGradient(colors: [
                                          AppTheme.secondary,
                                          AppTheme.primary
                                        ]),
                                        borderRadius: BorderRadius.circular(12),
                                        boxShadow: [
                                          BoxShadow(
                                              color: AppTheme.secondary
                                                  .withValues(alpha: 0.3),
                                              blurRadius: 8)
                                        ],
                                      )
                                    : AppTheme.modernCardDecoration(
                                        borderRadius: 12,
                                        color: AppTheme.surfaceLight
                                            .withOpacity(0.06)),
                                child: Center(
                                    child: Text('$m\'',
                                        style: TextStyle(
                                          color: duration == m
                                              ? Colors.white
                                              : AppTheme.textSecondary,
                                          fontWeight: FontWeight.bold,
                                          fontSize: 15,
                                        ))),
                              ),
                            ),
                          )),
                      ]),
                      const SizedBox(height: 20),

                      // Ghi chú
                      const Text('Ghi chú',
                          style: TextStyle(
                              fontWeight: FontWeight.w600,
                              color: AppTheme.secondary,
                              fontSize: 13,
                              letterSpacing: 0.5)),
                      const SizedBox(height: 8),
                      TextField(
                        controller: moTaController,
                        style: const TextStyle(
                            color: AppTheme.textPrimary, fontSize: 14),
                        decoration: InputDecoration(
                          hintText: 'VD: Buổi học thứ 5...',
                          hintStyle: TextStyle(
                              color: AppTheme.textMuted.withValues(alpha: 0.4)),
                          filled: true,
                          fillColor: Colors.white.withValues(alpha: 0.05),
                          border: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(14),
                              borderSide: BorderSide(
                                  color: Colors.white.withValues(alpha: 0.1))),
                          enabledBorder: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(14),
                              borderSide: BorderSide(
                                  color: Colors.white.withValues(alpha: 0.1))),
                          focusedBorder: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(14),
                              borderSide:
                                  const BorderSide(color: AppTheme.secondary)),
                        ),
                      ),
                      const SizedBox(height: 28),

                      // Nút tạo
                      SizedBox(
                          width: double.infinity,
                          height: 54,
                          child: ElevatedButton(
                            onPressed: selectedLopId == null
                                ? null
                                : () => _createSession(ctx, selectedLopId!,
                                    duration, moTaController.text),
                            style: ElevatedButton.styleFrom(
                              padding: EdgeInsets.zero,
                              shape: RoundedRectangleBorder(
                                  borderRadius: BorderRadius.circular(16)),
                              elevation: 0,
                            ),
                            child: Ink(
                              decoration: BoxDecoration(
                                gradient: selectedLopId != null
                                    ? const LinearGradient(colors: [
                                        AppTheme.success,
                                        Color(0xFF059669)
                                      ])
                                    : null,
                                color: selectedLopId == null
                                    ? AppTheme.surfaceLight
                                    : null,
                                borderRadius: BorderRadius.circular(16),
                              ),
                              child: Container(
                                alignment: Alignment.center,
                                child: Row(
                                    mainAxisAlignment: MainAxisAlignment.center,
                                    children: [
                                      Icon(Icons.play_circle_fill,
                                          size: 22,
                                          color: selectedLopId != null
                                              ? Colors.white
                                              : AppTheme.textMuted),
                                      const SizedBox(width: 8),
                                      Text('MỞ PHIÊN ĐIỂM DANH',
                                          style: TextStyle(
                                            fontWeight: FontWeight.bold,
                                            fontSize: 15,
                                            letterSpacing: 0.5,
                                            color: selectedLopId != null
                                                ? Colors.white
                                                : AppTheme.textMuted,
                                          )),
                                    ]),
                              ),
                            ),
                          )),
                      const SizedBox(height: 12),
                    ]),
              ),
            ),
          ),
        ),
      ),
    );
  }

  Future<void> _createSession(
      BuildContext ctx, int lopId, int duration, String moTa) async {
    Navigator.pop(ctx);
    setState(() => _isLoading = true);

    double? lat, lng;

    try {
      final result = await _api.createSession(lopId,
          durationMinutes: duration, moTa: moTa, lat: lat, lng: lng);
      if (mounted) {
        final success = result['success'] == true;
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content:
              Text(result['message'] ?? (success ? 'Thành công' : 'Thất bại')),
          backgroundColor: success ? AppTheme.success : AppTheme.error,
          behavior: SnackBarBehavior.floating,
          shape:
              RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        ));
        _loadSessions();
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text('Lỗi: $e'),
          backgroundColor: AppTheme.error,
          behavior: SnackBarBehavior.floating,
        ));
        setState(() => _isLoading = false);
      }
    }
  }

  Future<void> _stopSession(int sessionId) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppTheme.surface,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: const Text('Đóng phiên?',
            style: TextStyle(color: AppTheme.textPrimary)),
        content: const Text('Sinh viên sẽ không thể điểm danh phiên này nữa.',
            style: TextStyle(color: AppTheme.textSecondary)),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(ctx, false),
              child: const Text('Hủy',
                  style: TextStyle(color: AppTheme.textMuted))),
          TextButton(
              onPressed: () => Navigator.pop(ctx, true),
              child: const Text('Đóng phiên',
                  style: TextStyle(color: AppTheme.accent))),
        ],
      ),
    );
    if (confirm != true) return;

    try {
      final result = await _api.stopSession(sessionId);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text(result['message'] ?? 'Đã đóng phiên'),
          backgroundColor: AppTheme.success,
          behavior: SnackBarBehavior.floating,
          shape:
              RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        ));
        _loadSessions();
      }
    } catch (e) {
      if (mounted)
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text('Lỗi: $e')));
    }
  }

  // ====== BUILD ======
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      body: Stack(
        children: [
          Container(color: Theme.of(context).scaffoldBackgroundColor),
          SafeArea(
            child: Column(
              children: [
                _buildAppBar(),
                Expanded(
                  child: _isLoading
                      ? const Center(
                          child: CircularProgressIndicator(
                              color: AppTheme.secondary))
                      : RefreshIndicator(
                          color: AppTheme.secondary,
                          backgroundColor: AppTheme.surface,
                          onRefresh: _loadSessions,
                          child: _sessions.isEmpty
                              ? ListView(children: [
                                  SizedBox(
                                      height:
                                          MediaQuery.of(context).size.height *
                                              0.2),
                                  _buildEmptyState()
                                ])
                              : ListView.builder(
                                  padding:
                                      const EdgeInsets.fromLTRB(20, 8, 20, 100),
                                  itemCount: _sessions.length + 1,
                                  itemBuilder: (ctx, i) {
                                    if (i == 0) return _buildStatsHeader();
                                    return _buildSessionCard(
                                        _sessions[i - 1], i - 1);
                                  },
                                ),
                        ),
                ),
              ],
            ),
          ),
        ],
      ),
      floatingActionButton: Padding(
        padding: const EdgeInsets.only(
            bottom: 90), // Tránh bị khuất bởi BottomNavigationBar
        child: Container(
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(20),
            gradient: const LinearGradient(
                colors: [AppTheme.success, Color(0xFF059669)]),
            boxShadow: [
              BoxShadow(
                  color: AppTheme.success.withValues(alpha: 0.4),
                  blurRadius: 16,
                  offset: const Offset(0, 6))
            ],
          ),
          child: FloatingActionButton.extended(
            heroTag: 'admin_session_fab',
            onPressed: _showCreateDialog,
            backgroundColor: Colors.transparent,
            elevation: 0,
            icon: const Icon(Icons.add_circle, color: Colors.white),
            label: const Text('Mở phiên mới',
                style: TextStyle(
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                    letterSpacing: 0.5)),
          ),
        ).animate().fadeIn(delay: 500.ms).slideY(begin: 0.5, end: 0),
      ),
    );
  }

  Widget _buildAppBar() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                  colors: [AppTheme.success, Color(0xFF059669)]),
              borderRadius: BorderRadius.circular(12),
            ),
            child: const Icon(Icons.event_available,
                color: Colors.white, size: 20),
          ),
          const SizedBox(width: 12),
          const Expanded(
            child: Text('Phiên Điểm Danh',
                style: TextStyle(
                    color: AppTheme.textPrimary,
                    fontSize: 20,
                    fontWeight: FontWeight.bold)),
          ),
        ],
      ),
    ).animate().fadeIn(duration: 400.ms).slideY(begin: -0.2, end: 0);
  }

  Widget _buildStatsHeader() {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [Color(0xFF4F46E5), Color(0xFF7C3AED)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
              color: AppTheme.primary.withValues(alpha: 0.3),
              blurRadius: 16,
              offset: const Offset(0, 8))
        ],
      ),
      child: Row(children: [
        Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: 0.15),
              borderRadius: BorderRadius.circular(14)),
          child:
              const Icon(Icons.event_available, color: Colors.white, size: 28),
        ),
        const SizedBox(width: 16),
        Expanded(
            child:
                Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text('${_sessions.length} phiên đang mở',
              style: const TextStyle(
                  color: Colors.white,
                  fontSize: 20,
                  fontWeight: FontWeight.bold)),
          const SizedBox(height: 4),
          Text('Sinh viên có thể điểm danh ngay',
              style: TextStyle(
                  color: Colors.white.withValues(alpha: 0.7), fontSize: 13)),
        ])),
      ]),
    )
        .animate()
        .fadeIn(delay: 200.ms)
        .scale(begin: const Offset(0.95, 0.95), end: const Offset(1, 1));
  }

  Widget _buildSessionCard(AttendanceSession session, int index) {
    final remaining = session.thoiGianConLai;
    final remainingStr =
        remaining != null ? '${remaining.inMinutes} phút' : '∞';
    final isUrgent = remaining != null && remaining.inMinutes < 15;

    return GestureDetector(
      onTap: () => Navigator.push(
          context,
          MaterialPageRoute(
            builder: (_) => AdminSessionDetailScreen(
                sessionId: session.id, tenLop: session.tenLop),
          )),
      child: NeuContainer(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.all(18),
        borderRadius: 20,
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                    colors: isUrgent
                        ? [AppTheme.warning, const Color(0xFFD97706)]
                        : [AppTheme.success, const Color(0xFF059669)]),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Icon(isUrgent ? Icons.timer : Icons.class_,
                  color: Colors.white, size: 22),
            ),
            const SizedBox(width: 14),
            Expanded(
                child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                  Text(session.tenLop,
                      style: const TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 16,
                          color: AppTheme.textPrimary)),
                  const SizedBox(height: 2),
                  Text(session.maLop,
                      style: const TextStyle(
                          color: AppTheme.textMuted, fontSize: 12)),
                ])),
            GestureDetector(
              onTap: () => _showQRDialog(session),
              child: NeuContainer(
                padding: const EdgeInsets.all(8),
                shape: BoxShape.circle,
                child: const Icon(Icons.qr_code,
                    color: AppTheme.secondary, size: 20),
              ),
            ),
            const SizedBox(width: 8),
            GestureDetector(
              onTap: () => _stopSession(session.id),
              child: NeuContainer(
                padding: const EdgeInsets.all(8),
                shape: BoxShape.circle,
                isPressed: true,
                child: const Icon(Icons.stop_circle,
                    color: AppTheme.accent, size: 20),
              ),
            ),
          ]),
          const SizedBox(height: 14),
          // Chips row
          Wrap(spacing: 8, runSpacing: 8, children: [
            _chip(Icons.people, '${session.soDaDiemDanh} SV', AppTheme.success),
            _chip(Icons.timer, 'Còn $remainingStr',
                isUrgent ? AppTheme.warning : AppTheme.secondary),
            if (session.giaoVien != null && session.giaoVien!.isNotEmpty)
              _chip(Icons.person, session.giaoVien!, AppTheme.primary),
          ]),
          if (session.moTa != null && session.moTa!.isNotEmpty) ...[
            const SizedBox(height: 10),
            Text(session.moTa!,
                style: TextStyle(
                    color: AppTheme.textMuted.withValues(alpha: 0.6),
                    fontSize: 12,
                    fontStyle: FontStyle.italic)),
          ],
        ]),
      ),
    )
        .animate()
        .fadeIn(delay: Duration(milliseconds: 300 + (index * 100)))
        .slideX(begin: 0.1, end: 0);
  }

  void _showQRDialog(AttendanceSession session) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: AppTheme.surface,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
        title: Text('QR - ${session.maLop}',
            textAlign: TextAlign.center,
            style: const TextStyle(
                color: AppTheme.textPrimary, fontWeight: FontWeight.bold)),
        content: SizedBox(
          width: 250,
          height: 260,
          child: Column(children: [
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                  color: Colors.white, borderRadius: BorderRadius.circular(16)),
              child: QrImageView(
                  data: 'MTUFACE_SESSION_${session.id}',
                  version: QrVersions.auto,
                  size: 180),
            ),
            const SizedBox(height: 12),
            Text('Session #${session.id}',
                style:
                    const TextStyle(color: AppTheme.textMuted, fontSize: 12)),
          ]),
        ),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Đóng',
                  style: TextStyle(color: AppTheme.secondary))),
        ],
      ),
    );
  }

  Widget _chip(IconData icon, String text, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
          color: color.withValues(alpha: 0.12),
          borderRadius: BorderRadius.circular(10)),
      child: Row(mainAxisSize: MainAxisSize.min, children: [
        Icon(icon, size: 12, color: color),
        const SizedBox(width: 5),
        Text(text,
            style: TextStyle(
                fontSize: 11, color: color, fontWeight: FontWeight.w600)),
      ]),
    );
  }

  Widget _buildEmptyState() {
    return Column(mainAxisSize: MainAxisSize.min, children: [
      NeuContainer(
        padding: const EdgeInsets.all(28),
        shape: BoxShape.circle,
        child:
            const Icon(Icons.event_busy, color: AppTheme.secondary, size: 48),
      )
          .animate()
          .fadeIn(delay: 200.ms)
          .scale(begin: const Offset(0.5, 0.5), end: const Offset(1, 1)),
      const SizedBox(height: 20),
      const Text('Chưa có phiên nào đang mở',
              style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: AppTheme.textPrimary))
          .animate()
          .fadeIn(delay: 300.ms),
      const SizedBox(height: 8),
      Text('Nhấn nút bên dưới để mở phiên mới',
              style:
                  TextStyle(color: AppTheme.textMuted.withValues(alpha: 0.6)))
          .animate()
          .fadeIn(delay: 400.ms),
    ]);
  }
}
