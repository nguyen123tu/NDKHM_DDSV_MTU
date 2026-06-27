import 'dart:async';
import 'package:flutter/material.dart';
import 'package:connectivity_plus/connectivity_plus.dart';
import '../data/local/app_database.dart';
import '../services/sync_manager.dart';
import '../services/offline_queue_service.dart';
import 'package:flutter/foundation.dart';

/// Provider quản lý trạng thái kết nối mạng và đồng bộ.
/// Hiển thị banner offline/online trên UI, trigger sync khi có mạng trở lại.
class ConnectivityProvider with ChangeNotifier {
  bool _isOnline = true;
  bool _isSyncing = false;
  int _pendingSyncCount = 0;
  String? _lastSyncTime;
  String? _syncMessage;
  StreamSubscription? _connectivitySubscription;

  bool get isOnline => _isOnline;
  bool get isSyncing => _isSyncing;
  int get pendingSyncCount => _pendingSyncCount;
  String? get lastSyncTime => _lastSyncTime;
  String? get syncMessage => _syncMessage;

  ConnectivityProvider() {
    _initConnectivity();
    _startListening();
    refreshPendingCount();
  }

  /// Kiểm tra kết nối ban đầu
  Future<void> _initConnectivity() async {
    try {
      var result = await Connectivity().checkConnectivity();
      _updateConnectionStatus(result);
    } catch (e) {
      _isOnline = false;
      notifyListeners();
    }
  }

  /// Lắng nghe thay đổi kết nối liên tục
  void _startListening() {
    _connectivitySubscription = Connectivity().onConnectivityChanged.listen((result) {
      final wasOffline = !_isOnline;
      _updateConnectionStatus(result);

      // Chuyển từ offline → online → trigger sync tự động
      if (wasOffline && _isOnline) {
        triggerSync();
      }
    });
  }

  void _updateConnectionStatus(dynamic result) {
    if (result is List) {
      _isOnline = !result.contains(ConnectivityResult.none);
    } else {
      _isOnline = result.toString() != 'ConnectivityResult.none';
    }
    notifyListeners();
  }

  /// Kích hoạt đồng bộ toàn bộ (gọi từ listener hoặc UI)
  Future<void> triggerSync() async {
    if (_isSyncing || !_isOnline) return;

    _isSyncing = true;
    _syncMessage = 'Đang đồng bộ...';
    notifyListeners();

    try {
      // 1. Đẩy offline queue trước
      final queueResult = await OfflineQueueService.instance.processQueue();

      // 2. Sync dữ liệu chính (pull students, push attendance, pull sessions...)
      await SyncManager.instance.syncAll();

      // 3. Dọn dẹp queue đã hoàn thành
      await OfflineQueueService.instance.cleanCompleted();

      _lastSyncTime = _formatTime(DateTime.now());
      _syncMessage = 'Đã đồng bộ lúc $_lastSyncTime';

      if ((queueResult['success'] ?? 0) > 0) {
        _syncMessage = 'Đã đẩy ${queueResult['success']} bản ghi ✓';
      }
    } catch (e) {
      _syncMessage = 'Lỗi đồng bộ';
      debugPrint('[ConnectivityProvider] Sync error: $e');
    } finally {
      _isSyncing = false;
      await refreshPendingCount();
      notifyListeners();
    }
  }

  /// Sync thủ công (từ nút trên UI)
  Future<void> manualSync() async {
    if (!_isOnline) {
      _syncMessage = 'Không có kết nối mạng';
      notifyListeners();
      return;
    }
    await triggerSync();
  }

  /// Cập nhật số bản ghi chờ sync
  Future<void> refreshPendingCount() async {
    try {
      final queueCount = await OfflineQueueService.instance.getPendingCount();
      final attendanceCount = await _getPendingAttendanceCount();
      _pendingSyncCount = queueCount + attendanceCount;
    } catch (_) {
      _pendingSyncCount = 0;
    }
    notifyListeners();
  }

  /// Đếm attendance chưa sync (bảng local_attendance)
  Future<int> _getPendingAttendanceCount() async {
    try {
      final db = await AppDatabase.instance.database;
      final result = await db.rawQuery(
        'SELECT COUNT(*) as c FROM local_attendance WHERE sync_status = 0',
      );
      return result.first['c'] as int? ?? 0;
    } catch (_) {
      return 0;
    }
  }

  String _formatTime(DateTime dt) {
    return '${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}';
  }

  @override
  void dispose() {
    _connectivitySubscription?.cancel();
    super.dispose();
  }
}
