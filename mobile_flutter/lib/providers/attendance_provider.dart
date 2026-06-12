import 'package:flutter/material.dart';
import 'package:sqflite/sqflite.dart';
import 'package:connectivity_plus/connectivity_plus.dart';
import '../models/attendance_record.dart';
import '../services/api_service.dart';
import '../data/local/app_database.dart';

class AttendanceProvider with ChangeNotifier {
  final ApiService _apiService = ApiService();
  
  DashboardStats? _stats;
  List<AttendanceRecord> _history = [];
  bool _isLoading = false;
  bool _isOfflineData = false;
  String? _lastUpdateTime;

  DashboardStats? get stats => _stats;
  List<AttendanceRecord> get history => _history;
  bool get isLoading => _isLoading;
  bool get isOfflineData => _isOfflineData;
  String? get lastUpdateTime => _lastUpdateTime;

  Future<void> fetchDashboardData() async {
    _isLoading = true;
    notifyListeners();

    try {
      // ★ LUÔN load cache trước (hiển thị ngay, không chờ mạng)
      await _fetchOffline();
      _isLoading = false;
      notifyListeners();

      // Sau đó thử fetch online để cập nhật data mới nhất
      bool hasConnection = await _checkConnectivity();
      if (hasConnection) {
        await _fetchOnline();
        notifyListeners();
      }
    } catch (e) {
      debugPrint("Error fetching dashboard: $e");
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Fetch từ API (online) + cache vào SQLite
  Future<void> _fetchOnline() async {
    try {
      final statsData = await _apiService.getDashboardStats();
      if (statsData['success'] == true) {
        _stats = DashboardStats.fromJson(statsData['data']);
        await _cacheStats(statsData['data']);
      }

      final historyData = await _apiService.getHistory();
      if (historyData['success'] == true) {
        final List<dynamic> recordsRaw = historyData['data'];
        _history = recordsRaw.map((v) => AttendanceRecord.fromJson(v)).toList();
        await _cacheHistory(recordsRaw);
      }

      _isOfflineData = false;
      _lastUpdateTime = _formatTime(DateTime.now());
    } catch (e) {
      debugPrint("[AttendanceProvider] Online fetch failed: $e");
      await _fetchOffline();
    }
  }

  /// Fetch từ SQLite cache (offline fallback)
  Future<void> _fetchOffline() async {
    try {
      final db = await AppDatabase.instance.database;

      // Load cached stats
      final statsRows = await db.query('cached_stats');
      if (statsRows.isNotEmpty) {
        Map<String, dynamic> statsMap = {};
        for (var row in statsRows) {
          statsMap[row['key'] as String] = int.tryParse(row['value'] as String) ?? row['value'];
        }
        if (statsMap.isNotEmpty) {
          _stats = DashboardStats(
            total: statsMap['total'] ?? 0,
            present: statsMap['present'] ?? 0,
            absent: statsMap['absent'] ?? 0,
          );
        }
      }

      // Load cached history
      final historyRows = await db.query('cached_history', orderBy: 'thoi_gian DESC', limit: 20);
      if (historyRows.isNotEmpty) {
        _history = historyRows.map((row) => AttendanceRecord(
          id: row['id'] as int?,
          thoiGian: row['thoi_gian'] as String? ?? '',
          gioRa: row['gio_ra'] as String?,
          trangThai: row['trang_thai'] as String? ?? 'Unknown',
          hoTen: row['ho_ten'] as String? ?? 'Unknown',
          mssv: row['mssv'] as String? ?? '',
          maLop: row['ma_lop'] as String? ?? '',
          avatar: row['avatar'] as String?,
          evidencePath: row['evidence_path'] as String?,
        )).toList();
      }

      // Bổ sung pending offline attendance vào stats
      final pendingResult = await db.rawQuery(
        'SELECT COUNT(*) as c FROM local_attendance WHERE sync_status = 0',
      );
      final pendingCount = pendingResult.first['c'] as int? ?? 0;
      if (pendingCount > 0 && _stats != null) {
        _stats = DashboardStats(
          total: _stats!.total,
          present: _stats!.present + pendingCount,
          absent: _stats!.absent > pendingCount ? _stats!.absent - pendingCount : 0,
        );
      }

      _isOfflineData = true;

      if (statsRows.isNotEmpty) {
        _lastUpdateTime = statsRows.first['updated_at'] as String?;
        if (_lastUpdateTime != null && _lastUpdateTime!.length > 16) {
          _lastUpdateTime = _lastUpdateTime!.substring(11, 16);
        }
      }
    } catch (e) {
      debugPrint("[AttendanceProvider] Offline fetch failed: $e");
    }
  }

  /// Cache stats vào SQLite
  Future<void> _cacheStats(Map<String, dynamic> statsData) async {
    try {
      final db = await AppDatabase.instance.database;
      final now = DateTime.now().toIso8601String();
      final batch = db.batch();

      for (var entry in statsData.entries) {
        batch.insert(
          'cached_stats',
          {'key': entry.key, 'value': entry.value.toString(), 'updated_at': now},
          conflictAlgorithm: ConflictAlgorithm.replace,
        );
      }
      await batch.commit(noResult: true);
    } catch (e) {
      debugPrint("[AttendanceProvider] Cache stats error: $e");
    }
  }

  /// Cache history vào SQLite
  Future<void> _cacheHistory(List<dynamic> records) async {
    try {
      final db = await AppDatabase.instance.database;
      await db.delete('cached_history');

      final batch = db.batch();
      for (var record in records) {
        batch.insert('cached_history', {
          'id': record['id'],
          'ho_ten': record['ho_ten'],
          'mssv': record['mssv'],
          'ma_lop': record['ma_lop'],
          'thoi_gian': record['thoi_gian'],
          'gio_ra': record['gio_ra'],
          'trang_thai': record['trang_thai'],
          'avatar': record['avatar'],
          'evidence_path': record['evidence_path'],
        }, conflictAlgorithm: ConflictAlgorithm.replace);
      }
      await batch.commit(noResult: true);
    } catch (e) {
      debugPrint("[AttendanceProvider] Cache history error: $e");
    }
  }

  Future<bool> _checkConnectivity() async {
    try {
      final result = await Connectivity().checkConnectivity();
      return !result.contains(ConnectivityResult.none);
    } catch (_) {
      return false;
    }
  }

  String _formatTime(DateTime dt) {
    return '${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}';
  }

  /// Refresh lại dashboard (gọi sau khi quét mặt thành công)
  Future<void> refreshHistory() async {
    await fetchDashboardData();
  }
}
