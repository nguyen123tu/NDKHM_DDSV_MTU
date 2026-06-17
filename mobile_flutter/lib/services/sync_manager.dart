import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:sqflite/sqflite.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:connectivity_plus/connectivity_plus.dart';
import '../data/repositories/student_repository.dart';
import '../data/repositories/attendance_repository.dart';
import '../data/repositories/session_repository.dart';
import '../data/repositories/schedule_repository.dart';
import '../data/repositories/notification_repository.dart';
import '../data/local/app_database.dart';
import 'api_service.dart';
import 'offline_queue_service.dart';

class SyncManager {
  static final SyncManager instance = SyncManager._internal();
  SyncManager._internal();

  final StudentRepository _studentRepo = StudentRepository();
  final AttendanceRepository _attendanceRepo = AttendanceRepository();
  final SessionRepository _sessionRepo = SessionRepository();
  final ScheduleRepository _scheduleRepo = ScheduleRepository();
  final NotificationRepository _notificationRepo = NotificationRepository();
  bool _isSyncing = false;

  /// Gọi hàm này để chạy toàn bộ tiến trình đồng bộ
  Future<void> syncAll() async {
    if (_isSyncing) return;

    // Kiểm tra kết nối mạng
    var connectivityResult = await (Connectivity().checkConnectivity());
    bool hasConnection = true;
    hasConnection = !connectivityResult.contains(ConnectivityResult.none);
  
    if (!hasConnection) {
      print('[SYNC] Không có mạng. Bỏ qua đồng bộ.');
      return;
    }

    _isSyncing = true;
    print('[SYNC] ═══════════════════════════════════════');
    print('[SYNC] Bắt đầu tiến trình đồng bộ ngầm...');
    
    // PUSH trước (đẩy data offline lên server)
    await pushAttendance();
    await OfflineQueueService.instance.processQueue();

    // PULL sau (tải data mới về)
    await pullStudents();
    await pullSessions();
    await pullSchedule();
    await pullNotifications();

    // Dọn dẹp
    await OfflineQueueService.instance.cleanCompleted();
    await _updateSyncMetadata();

    print('[SYNC] Hoàn tất đồng bộ.');
    print('[SYNC] ═══════════════════════════════════════');
    _isSyncing = false;
  }

  // ================================================================
  // PULL: Tải dữ liệu từ server về local
  // ================================================================

  /// PULL: Tải danh sách sinh viên & Vector khuôn mặt từ Server
  Future<void> pullStudents() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final lastSyncTime = prefs.getString('last_sync_time') ?? '1970-01-01 00:00:00';
      final token = prefs.getString('auth_token');

      final response = await http.get(
        Uri.parse('${ApiService.baseUrl}/api/mobile/sync/students?last_sync_time=$lastSyncTime'),
        headers: {
          'Content-Type': 'application/json',
          if (token != null) 'Authorization': 'Bearer $token',
        },
      ).timeout(const Duration(seconds: 30));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['success'] == true) {
          final List<dynamic> students = data['data'];
          if (students.isNotEmpty) {
            await _studentRepo.insertMultipleStudents(students);
          }
          final serverTime = data['server_time'];
          await prefs.setString('last_sync_time', serverTime);
          print('[SYNC PULL] ✓ Sinh viên: ${students.length} bản ghi. Time: $serverTime');
        }
      }
    } catch (e) {
      print('[SYNC PULL ERROR] Students: $e');
    }
  }

  /// PULL: Tải phiên điểm danh đang mở từ Server
  Future<void> pullSessions() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final token = prefs.getString('auth_token');

      final response = await http.get(
        Uri.parse('${ApiService.baseUrl}/api/mobile/sessions/active'),
        headers: {
          'Content-Type': 'application/json',
          if (token != null) 'Authorization': 'Bearer $token',
        },
      ).timeout(const Duration(seconds: 15));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['success'] == true) {
          final List<dynamic> sessions = data['data'];
          await _sessionRepo.upsertSessions(sessions);
          print('[SYNC PULL] ✓ Phiên điểm danh: ${sessions.length} phiên đang mở');
        }
      }
    } catch (e) {
      print('[SYNC PULL ERROR] Sessions: $e');
    }
  }

  /// PULL: Tải lịch học từ Server
  Future<void> pullSchedule() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final token = prefs.getString('auth_token');
      final role = prefs.getString('auth_role');

      // Chỉ sinh viên mới có lịch học
      if (role != 'student') return;

      final response = await http.get(
        Uri.parse('${ApiService.baseUrl}/api/mobile/schedule'),
        headers: {
          'Content-Type': 'application/json',
          if (token != null) 'Authorization': 'Bearer $token',
        },
      ).timeout(const Duration(seconds: 15));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['success'] == true) {
          final List<dynamic> schedules = data['data'];
          await _scheduleRepo.replaceSchedules(schedules);
          print('[SYNC PULL] ✓ Lịch học: ${schedules.length} buổi');
        }
      }
    } catch (e) {
      print('[SYNC PULL ERROR] Schedule: $e');
    }
  }

  /// PULL: Tải thông báo từ Server
  Future<void> pullNotifications() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final token = prefs.getString('auth_token');

      final response = await http.get(
        Uri.parse('${ApiService.baseUrl}/api/mobile/notifications'),
        headers: {
          'Content-Type': 'application/json',
          if (token != null) 'Authorization': 'Bearer $token',
        },
      ).timeout(const Duration(seconds: 15));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['success'] == true) {
          final List<dynamic> notifications = data['data'];
          await _notificationRepo.upsertNotifications(notifications);
          print('[SYNC PULL] ✓ Thông báo: ${notifications.length} tin');
        }
      }
    } catch (e) {
      print('[SYNC PULL ERROR] Notifications: $e');
    }
  }

  // ================================================================
  // PUSH: Đẩy dữ liệu offline lên server
  // ================================================================

  /// PUSH: Đẩy lịch sử điểm danh lúc Offline lên Server
  Future<void> pushAttendance() async {
    try {
      final pendingLogs = await _attendanceRepo.getPendingLogs();
      if (pendingLogs.isEmpty) return;

      final prefs = await SharedPreferences.getInstance();
      final token = prefs.getString('auth_token');

      final response = await http.post(
        Uri.parse('${ApiService.baseUrl}/api/mobile/sync/attendance'),
        headers: {
          'Content-Type': 'application/json',
          if (token != null) 'Authorization': 'Bearer $token',
        },
        body: jsonEncode({'logs': pendingLogs}),
      ).timeout(const Duration(seconds: 30));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['success'] == true) {
          final List<dynamic> syncedUuids = data['synced_local_uuids'] ?? [];
          final List<dynamic> errors = data['errors'] ?? [];
          
          final List<String> uuidsToRemove = syncedUuids.cast<String>().toList();
          
          // Lấy luôn các UUID bị lỗi (ví dụ: "Sinh viên không tồn tại" hoặc "OFFLINE_PENDING")
          // Để xóa khỏi hàng đợi, tránh việc app kẹt đồng bộ và thử lại mãi mãi.
          for (var err in errors) {
            if (err['local_uuid'] != null) {
              uuidsToRemove.add(err['local_uuid'].toString());
            }
          }

          if (uuidsToRemove.isNotEmpty) {
            await _attendanceRepo.markAsSynced(uuidsToRemove);
            print('[SYNC PUSH] ✓ Đã dọn dẹp ${uuidsToRemove.length} lượt điểm danh (Thành công: ${syncedUuids.length}, Lỗi: ${errors.length})');
          }
        }
      }
    } catch (e) {
      print('[SYNC PUSH ERROR] Attendance: $e');
    }
  }

  // ================================================================
  // METADATA & UTILITIES
  // ================================================================

  /// Cập nhật metadata đồng bộ
  Future<void> _updateSyncMetadata() async {
    try {
      final db = await AppDatabase.instance.database;
      final now = DateTime.now().toIso8601String();

      await db.insert('sync_metadata', {
        'data_type': 'full_sync',
        'last_sync_time': now,
        'last_sync_status': 'success',
      }, conflictAlgorithm: ConflictAlgorithm.replace);
    } catch (e) {
      print('[SYNC META ERROR] $e');
    }
  }

  /// Lấy thời gian sync cuối cùng
  Future<String?> getLastSyncTime() async {
    try {
      final db = await AppDatabase.instance.database;
      final result = await db.query(
        'sync_metadata',
        where: 'data_type = ?',
        whereArgs: ['full_sync'],
      );
      if (result.isNotEmpty) {
        return result.first['last_sync_time'] as String?;
      }
    } catch (_) {}
    return null;
  }

  /// Khởi tạo Listener lắng nghe thay đổi mạng
  void initializeNetworkListener() {
    Connectivity().onConnectivityChanged.listen((result) {
      bool hasConnection = true;
      hasConnection = !result.contains(ConnectivityResult.none);
    
      if (hasConnection) {
        print('[NETWORK] Đã kết nối Internet. Kích hoạt Sync ngầm...');
        syncAll();
      }
    });
  }
}
