import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../services/export_service.dart';
import 'admin_session_detail_screen.dart';

/// Màn hình Lịch sử phiên điểm danh (các phiên đã đóng)
class SessionHistoryScreen extends StatefulWidget {
  const SessionHistoryScreen({super.key});
  @override
  State<SessionHistoryScreen> createState() => _SessionHistoryScreenState();
}

class _SessionHistoryScreenState extends State<SessionHistoryScreen> {
  final ApiService _api = ApiService();
  List<dynamic> _sessions = [];
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadHistory();
  }

  Future<void> _loadHistory() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });
    try {
      final result = await _api.getSessionHistory();
      if (mounted) {
        if (result['success'] == true) {
          setState(() {
            _sessions = result['data'] ?? [];
            _isLoading = false;
          });
        } else {
          setState(() {
            _error = result['message'];
            _isLoading = false;
          });
        }
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = 'Lỗi kết nối: $e';
          _isLoading = false;
        });
      }
    }
  }

  Future<void> _deleteSession(int sessionId, String tenLop) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Row(
          children: [
            Icon(Icons.warning_amber_rounded, color: Colors.redAccent, size: 28),
            SizedBox(width: 8),
            Text('Xác nhận xóa'),
          ],
        ),
        content: Text(
          'Bạn có chắc muốn xóa phiên "$tenLop"?\n\nĐiều này sẽ xóa cả dữ liệu điểm danh của sinh viên trong phiên này.',
          style: const TextStyle(fontSize: 14),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Hủy'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(ctx, true),
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.redAccent,
              foregroundColor: Colors.white,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
            ),
            child: const Text('Xóa'),
          ),
        ],
      ),
    );

    if (confirm == true) {
      try {
        final result = await _api.deleteSession(sessionId);
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content: Text(result['message'] ?? 'Đã xóa'),
            backgroundColor: result['success'] == true ? Colors.green : Colors.red,
          ));
          if (result['success'] == true) {
            _loadHistory();
          }
        }
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content: Text('Lỗi: $e'),
            backgroundColor: Colors.red,
          ));
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF0F4F8),
      appBar: AppBar(
        title: const Text('Lịch sử điểm danh', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
        backgroundColor: const Color(0xFF1B3A5C),
        foregroundColor: Colors.white,
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _loadHistory),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: Color(0xFF1B3A5C)))
          : _error != null
              ? Center(child: Column(mainAxisSize: MainAxisSize.min, children: [
                  const Icon(Icons.error_outline, size: 48, color: Colors.red),
                  const SizedBox(height: 12),
                  Text(_error!, style: const TextStyle(color: Colors.red)),
                  const SizedBox(height: 12),
                  ElevatedButton(onPressed: _loadHistory, child: const Text('Thử lại')),
                ]))
              : _sessions.isEmpty
                  ? _buildEmptyState()
                  : RefreshIndicator(
                      onRefresh: _loadHistory,
                      child: ListView.builder(
                        padding: const EdgeInsets.all(16),
                        itemCount: _sessions.length,
                        itemBuilder: (context, index) => _buildSessionCard(_sessions[index]),
                      ),
                    ),
    );
  }

  Widget _buildEmptyState() {
    return Center(child: Column(mainAxisSize: MainAxisSize.min, children: [
      Container(
        padding: const EdgeInsets.all(24),
        decoration: BoxDecoration(color: const Color(0xFF1B3A5C).withOpacity(0.06), shape: BoxShape.circle),
        child: const Icon(Icons.history, color: Color(0xFF1B3A5C), size: 48),
      ),
      const SizedBox(height: 20),
      const Text('Chưa có lịch sử', style: TextStyle(fontSize: 17, fontWeight: FontWeight.bold, color: Color(0xFF1B3A5C))),
      const SizedBox(height: 8),
      Text('Các phiên điểm danh đã đóng sẽ hiển thị ở đây',
          style: TextStyle(color: const Color(0xFF1B3A5C).withOpacity(0.5), fontSize: 14)),
    ]));
  }

  Widget _buildSessionCard(Map<String, dynamic> session) {
    final int present = session['so_da_diem_danh'] ?? 0;
    final int total = session['tong_sv'] ?? 0;
    final int absent = total - present;
    final String tenLop = session['ten_lop'] ?? '';
    final String maLop = session['ma_lop'] ?? '';
    final String batDau = session['bat_dau'] ?? '';
    final String ketThuc = session['ket_thuc'] ?? '';

    // Format date for display
    String dateDisplay = '';
    String timeDisplay = '';
    try {
      final dt = DateTime.parse(batDau);
      dateDisplay = '${dt.day.toString().padLeft(2, '0')}/${dt.month.toString().padLeft(2, '0')}/${dt.year}';
      timeDisplay = '${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}';
      if (ketThuc.isNotEmpty) {
        final dtEnd = DateTime.parse(ketThuc);
        timeDisplay += ' - ${dtEnd.hour.toString().padLeft(2, '0')}:${dtEnd.minute.toString().padLeft(2, '0')}';
      }
    } catch (_) {}

    return GestureDetector(
      onTap: () {
        Navigator.push(context, MaterialPageRoute(
          builder: (_) => AdminSessionDetailScreen(sessionId: session['id'], tenLop: tenLop),
        ));
      },
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
          boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.04), blurRadius: 10, offset: const Offset(0, 4))],
        ),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            // Icon
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: const Color(0xFF6366F1).withOpacity(0.1),
                borderRadius: BorderRadius.circular(12),
              ),
              child: const Icon(Icons.history, color: Color(0xFF6366F1), size: 24),
            ),
            const SizedBox(width: 14),
            // Tên lớp
            Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(tenLop, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: Color(0xFF1B3A5C))),
              const SizedBox(height: 2),
              Text(maLop, style: TextStyle(color: const Color(0xFF1B3A5C).withOpacity(0.5), fontSize: 12)),
            ])),
            // Nút xóa
            GestureDetector(
              onTap: () => _deleteSession(session['id'], tenLop),
              child: Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: Colors.redAccent.withOpacity(0.08),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: const Icon(Icons.delete_outline, color: Colors.redAccent, size: 20),
              ),
            ),
          ]),
          const SizedBox(height: 12),
          // Thông tin chi tiết
          Row(children: [
            _infoChip(Icons.calendar_today, dateDisplay, const Color(0xFF6366F1)),
            const SizedBox(width: 8),
            _infoChip(Icons.access_time, timeDisplay, const Color(0xFF2E96EB)),
          ]),
          const SizedBox(height: 8),
          Row(children: [
            _infoChip(Icons.people, '$total SV', const Color(0xFF1B3A5C)),
            const SizedBox(width: 8),
            _infoChip(Icons.check_circle, '$present có mặt', const Color(0xFF10B981)),
            const SizedBox(width: 8),
            _infoChip(Icons.cancel, '$absent vắng', Colors.redAccent),
          ]),
        ]),
      ),
    );
  }

  Widget _infoChip(IconData icon, String text, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(color: color.withOpacity(0.08), borderRadius: BorderRadius.circular(8)),
      child: Row(mainAxisSize: MainAxisSize.min, children: [
        Icon(icon, size: 12, color: color),
        const SizedBox(width: 4),
        Flexible(child: Text(text, style: TextStyle(fontSize: 11, color: color, fontWeight: FontWeight.w600), overflow: TextOverflow.ellipsis)),
      ]),
    );
  }
}
