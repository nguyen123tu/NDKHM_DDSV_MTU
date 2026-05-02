import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:connectivity_plus/connectivity_plus.dart';
import '../data/repositories/student_repository.dart';
import '../data/repositories/attendance_repository.dart';
import 'api_service.dart';

class SyncManager {
  static final SyncManager instance = SyncManager._internal();
  SyncManager._internal();

  final StudentRepository _studentRepo = StudentRepository();
  final AttendanceRepository _attendanceRepo = AttendanceRepository();
  bool _isSyncing = false;

  /// Gọi hàm này để chạy toàn bộ tiến trình đồng bộ
  Future<void> syncAll() async {
    if (_isSyncing) return;

    // Kiểm tra kết nối mạng
    var connectivityResult = await (Connectivity().checkConnectivity());
    bool hasConnection = true;
    if (connectivityResult is List) {
      hasConnection = !connectivityResult.contains(ConnectivityResult.none);
    } else {
      hasConnection = connectivityResult.toString() != 'ConnectivityResult.none';
    }

    if (!hasConnection) {
      print('[SYNC] Không có mạng. Bỏ qua đồng bộ.');
      return;
    }

    _isSyncing = true;
    print('[SYNC] Bắt đầu tiến trình đồng bộ ngầm...');
    
    await pushAttendance(); // Đẩy log lên trước
    await pullStudents();   // Tải data mới về sau

    print('[SYNC] Hoàn tất đồng bộ.');
    _isSyncing = false;
  }

  /// PULL: Tải danh sách sinh viên & Vector khuôn mặt từ Server
  Future<void> pullStudents() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      // Mặc định lấy từ năm 1970 để tải full lần đầu
      final lastSyncTime = prefs.getString('last_sync_time') ?? '1970-01-01 00:00:00';

      final response = await http.get(
        Uri.parse('${ApiService.baseUrl}/api/mobile/sync/students?last_sync_time=$lastSyncTime'),
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
          print('[SYNC PULL] Đã tải về ${students.length} sinh viên mới. Time: $serverTime');
        }
      }
    } catch (e) {
      print('[SYNC PULL ERROR] $e');
    }
  }

  /// PUSH: Đẩy lịch sử điểm danh lúc Offline lên Server
  Future<void> pushAttendance() async {
    try {
      final pendingLogs = await _attendanceRepo.getPendingLogs();
      if (pendingLogs.isEmpty) return;

      final response = await http.post(
        Uri.parse('${ApiService.baseUrl}/api/mobile/sync/attendance'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'logs': pendingLogs}),
      ).timeout(const Duration(seconds: 30));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['success'] == true) {
          final List<dynamic> syncedUuids = data['synced_local_uuids'];
          if (syncedUuids.isNotEmpty) {
            await _attendanceRepo.markAsSynced(syncedUuids.cast<String>());
            print('[SYNC PUSH] Đã đẩy thành công ${syncedUuids.length} lượt điểm danh.');
          }
        }
      }
    } catch (e) {
      print('[SYNC PUSH ERROR] $e');
    }
  }

  /// Khởi tạo Listener lắng nghe thay đổi mạng
  void initializeNetworkListener() {
    Connectivity().onConnectivityChanged.listen((result) {
      bool hasConnection = true;
      if (result is List) {
        hasConnection = !result.contains(ConnectivityResult.none);
      } else {
        hasConnection = result.toString() != 'ConnectivityResult.none';
      }

      if (hasConnection) {
        print('[NETWORK] Đã kết nối Internet. Kích hoạt Sync ngầm...');
        syncAll();
      }
    });
  }
}
