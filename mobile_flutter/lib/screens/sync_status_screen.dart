import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/connectivity_provider.dart';
import '../services/sync_manager.dart';
import '../services/offline_queue_service.dart';
import '../data/local/app_database.dart';

/// Màn hình chi tiết trạng thái đồng bộ
class SyncStatusScreen extends StatefulWidget {
  const SyncStatusScreen({super.key});

  @override
  State<SyncStatusScreen> createState() => _SyncStatusScreenState();
}

class _SyncStatusScreenState extends State<SyncStatusScreen> {
  Map<String, int> _queueStats = {};
  int _pendingAttendance = 0;
  int _localStudents = 0;
  int _localSessions = 0;
  String? _lastSyncTime;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadStats();
  }

  Future<void> _loadStats() async {
    setState(() => _isLoading = true);

    try {
      final queueStats = await OfflineQueueService.instance.getQueueStats();
      final lastSync = await SyncManager.instance.getLastSyncTime();

      final db = await AppDatabase.instance.database;

      final pendingResult = await db.rawQuery(
        'SELECT COUNT(*) as c FROM local_attendance WHERE sync_status = 0',
      );
      final studentResult = await db.rawQuery(
        'SELECT COUNT(*) as c FROM local_students',
      );
      final sessionResult = await db.rawQuery(
        'SELECT COUNT(*) as c FROM local_sessions',
      );

      if (mounted) {
        setState(() {
          _queueStats = queueStats;
          _pendingAttendance = pendingResult.first['c'] as int? ?? 0;
          _localStudents = studentResult.first['c'] as int? ?? 0;
          _localSessions = sessionResult.first['c'] as int? ?? 0;
          _lastSyncTime = lastSync;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final connectivity = Provider.of<ConnectivityProvider>(context);

    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        title: const Text('Trạng thái đồng bộ',
            style: TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: Colors.white,
        foregroundColor: const Color(0xFF1E293B),
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadStats,
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _loadStats,
              child: ListView(
                padding: const EdgeInsets.all(20),
                children: [
                  // ====== TRẠNG THÁI KẾT NỐI ======
                  _buildConnectionCard(connectivity),
                  const SizedBox(height: 16),

                  // ====== THỐNG KÊ DỮ LIỆU LOCAL ======
                  _buildSectionTitle('Dữ liệu cục bộ'),
                  const SizedBox(height: 10),
                  Row(
                    children: [
                      Expanded(
                          child: _buildDataCard(
                        icon: Icons.people,
                        title: 'Sinh viên',
                        value: '$_localStudents',
                        color: const Color(0xFF4F46E5),
                      )),
                      const SizedBox(width: 12),
                      Expanded(
                          child: _buildDataCard(
                        icon: Icons.event,
                        title: 'Phiên ĐD',
                        value: '$_localSessions',
                        color: const Color(0xFF10B981),
                      )),
                    ],
                  ),
                  const SizedBox(height: 16),

                  // ====== HÀNG ĐỢI ĐỒNG BỘ ======
                  _buildSectionTitle('Hàng đợi đồng bộ'),
                  const SizedBox(height: 10),
                  _buildQueueItem(
                    icon: Icons.fingerprint,
                    title: 'Điểm danh chờ sync',
                    count: _pendingAttendance,
                    color: const Color(0xFFF59E0B),
                  ),
                  _buildQueueItem(
                    icon: Icons.pending_actions,
                    title: 'Thao tác offline chờ',
                    count: _queueStats['pending'] ?? 0,
                    color: const Color(0xFF2E96EB),
                  ),
                  _buildQueueItem(
                    icon: Icons.check_circle,
                    title: 'Đã hoàn thành',
                    count: _queueStats['completed'] ?? 0,
                    color: const Color(0xFF10B981),
                  ),
                  _buildQueueItem(
                    icon: Icons.error_outline,
                    title: 'Thất bại',
                    count: _queueStats['failed'] ?? 0,
                    color: Colors.redAccent,
                  ),
                  const SizedBox(height: 24),

                  // ====== NÚT SYNC ======
                  if (connectivity.isOnline)
                    SizedBox(
                      width: double.infinity,
                      height: 52,
                      child: ElevatedButton.icon(
                        onPressed: connectivity.isSyncing
                            ? null
                            : () async {
                                await connectivity.manualSync();
                                await _loadStats();
                              },
                        icon: connectivity.isSyncing
                            ? const SizedBox(
                                width: 20,
                                height: 20,
                                child: CircularProgressIndicator(
                                    color: Colors.white, strokeWidth: 2),
                              )
                            : const Icon(Icons.sync),
                        label: Text(
                          connectivity.isSyncing
                              ? 'Đang đồng bộ...'
                              : 'Đồng bộ ngay',
                          style: const TextStyle(
                              fontWeight: FontWeight.bold, fontSize: 15),
                        ),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: const Color(0xFF4F46E5),
                          foregroundColor: Colors.white,
                          shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(14)),
                          elevation: 2,
                        ),
                      ),
                    )
                  else
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: Colors.redAccent.withValues(alpha: 0.1),
                        borderRadius: BorderRadius.circular(14),
                        border: Border.all(
                            color: Colors.redAccent.withValues(alpha: 0.3)),
                      ),
                      child: const Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.wifi_off,
                              color: Colors.redAccent, size: 20),
                          SizedBox(width: 10),
                          Text(
                            'Kết nối Internet để đồng bộ',
                            style: TextStyle(
                                color: Colors.redAccent,
                                fontWeight: FontWeight.w600),
                          ),
                        ],
                      ),
                    ),

                  const SizedBox(height: 16),

                  // ====== THÔNG TIN SYNC ======
                  if (_lastSyncTime != null)
                    Container(
                      padding: const EdgeInsets.all(14),
                      decoration: BoxDecoration(
                        color: const Color(0xFF1E293B).withValues(alpha: 0.04),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Row(
                        children: [
                          const Icon(Icons.access_time,
                              size: 16, color: Color(0xFF94A3B8)),
                          const SizedBox(width: 8),
                          Text(
                            'Sync lần cuối: ${_formatSyncTime(_lastSyncTime!)}',
                            style: const TextStyle(
                                fontSize: 13, color: Color(0xFF94A3B8)),
                          ),
                        ],
                      ),
                    ),
                ],
              ),
            ),
    );
  }

  Widget _buildConnectionCard(ConnectivityProvider connectivity) {
    final isOnline = connectivity.isOnline;
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: isOnline
              ? [const Color(0xFF10B981), const Color(0xFF059669)]
              : [const Color(0xFFDC2626), const Color(0xFFB91C1C)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(18),
        boxShadow: [
          BoxShadow(
            color:
                (isOnline ? const Color(0xFF10B981) : const Color(0xFFDC2626))
                    .withValues(alpha: 0.3),
            blurRadius: 16,
            offset: const Offset(0, 6),
          ),
        ],
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
              isOnline ? Icons.wifi : Icons.wifi_off,
              color: Colors.white,
              size: 28,
            ),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  isOnline ? 'Đang kết nối' : 'Mất kết nối',
                  style: const TextStyle(
                      color: Colors.white,
                      fontSize: 18,
                      fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 4),
                Text(
                  isOnline
                      ? 'Dữ liệu sẽ được đồng bộ tự động'
                      : 'Dữ liệu được lưu cục bộ trên thiết bị',
                  style: TextStyle(
                      color: Colors.white.withValues(alpha: 0.8), fontSize: 13),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSectionTitle(String title) {
    return Text(
      title,
      style: const TextStyle(
          fontSize: 16, fontWeight: FontWeight.bold, color: Color(0xFF1E293B)),
    );
  }

  Widget _buildDataCard({
    required IconData icon,
    required String title,
    required String value,
    required Color color,
  }) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(14),
        boxShadow: [
          BoxShadow(
              color: Colors.black.withValues(alpha: 0.04),
              blurRadius: 10,
              offset: const Offset(0, 2))
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: color.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Icon(icon, color: color, size: 20),
          ),
          const SizedBox(height: 12),
          Text(value,
              style: TextStyle(
                  fontSize: 24, fontWeight: FontWeight.bold, color: color)),
          const SizedBox(height: 2),
          Text(title,
              style: const TextStyle(fontSize: 12, color: Color(0xFF94A3B8))),
        ],
      ),
    );
  }

  Widget _buildQueueItem({
    required IconData icon,
    required String title,
    required int count,
    required Color color,
  }) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
              color: Colors.black.withValues(alpha: 0.03),
              blurRadius: 6,
              offset: const Offset(0, 2))
        ],
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: color.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Icon(icon, color: color, size: 18),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Text(title,
                style: const TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w500,
                    color: Color(0xFF1E293B))),
          ),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
            decoration: BoxDecoration(
              color: count > 0
                  ? color.withValues(alpha: 0.1)
                  : const Color(0xFFF1F5F9),
              borderRadius: BorderRadius.circular(20),
            ),
            child: Text(
              '$count',
              style: TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.bold,
                color: count > 0 ? color : const Color(0xFF94A3B8),
              ),
            ),
          ),
        ],
      ),
    );
  }

  String _formatSyncTime(String isoTime) {
    try {
      final dt = DateTime.parse(isoTime);
      final now = DateTime.now();
      final diff = now.difference(dt);

      if (diff.inMinutes < 1) return 'Vừa xong';
      if (diff.inMinutes < 60) return '${diff.inMinutes} phút trước';
      if (diff.inHours < 24) return '${diff.inHours} giờ trước';
      return '${dt.day}/${dt.month} lúc ${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}';
    } catch (_) {
      return isoTime;
    }
  }
}
