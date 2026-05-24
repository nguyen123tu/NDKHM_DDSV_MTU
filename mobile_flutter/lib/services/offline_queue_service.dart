import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:uuid/uuid.dart';
import '../data/local/app_database.dart';
import 'api_service.dart';

/// Command Queue Pattern: Mọi thao tác write đều qua đây.
/// Online → execute ngay. Offline → lưu vào SQLite → sync khi có mạng.
class OfflineQueueService {
  static final OfflineQueueService instance = OfflineQueueService._internal();
  OfflineQueueService._internal();

  final AppDatabase _appDatabase = AppDatabase.instance;
  final _uuid = const Uuid();

  /// Thêm một thao tác vào hàng đợi offline
  Future<String> enqueue({
    required String actionType,
    required String endpoint,
    required String method,
    required Map<String, dynamic> payload,
  }) async {
    final db = await _appDatabase.database;
    final localUuid = _uuid.v4();

    await db.insert('offline_queue', {
      'local_uuid': localUuid,
      'action_type': actionType,
      'endpoint': endpoint,
      'method': method,
      'payload': jsonEncode(payload),
      'created_at': DateTime.now().toIso8601String(),
      'retry_count': 0,
      'max_retries': 5,
      'status': 'pending',
    });

    print('[QUEUE] Đã thêm: $actionType (UUID: $localUuid)');
    return localUuid;
  }

  /// Lấy tất cả thao tác đang chờ
  Future<List<Map<String, dynamic>>> getPendingActions() async {
    final db = await _appDatabase.database;
    return await db.query(
      'offline_queue',
      where: 'status = ? AND retry_count < max_retries',
      whereArgs: ['pending'],
      orderBy: 'created_at ASC',
    );
  }

  /// Đếm số thao tác đang chờ
  Future<int> getPendingCount() async {
    final db = await _appDatabase.database;
    final result = await db.rawQuery(
      'SELECT COUNT(*) as count FROM offline_queue WHERE status = ?',
      ['pending'],
    );
    return result.first['count'] as int? ?? 0;
  }

  /// Thực thi tất cả thao tác trong hàng đợi
  Future<Map<String, int>> processQueue() async {
    final pendingActions = await getPendingActions();
    if (pendingActions.isEmpty) return {'success': 0, 'failed': 0};

    int successCount = 0;
    int failedCount = 0;

    for (var action in pendingActions) {
      try {
        final success = await _executeAction(action);
        if (success) {
          await _markCompleted(action['id'] as int);
          successCount++;
        } else {
          await _incrementRetry(action['id'] as int, 'Server trả về lỗi hoặc Token hết hạn');
          failedCount++;
        }
      } catch (e) {
        await _incrementRetry(action['id'] as int, e.toString());
        failedCount++;
      }
    }

    print('[QUEUE] Xử lý xong: $successCount thành công, $failedCount thất bại');
    return {'success': successCount, 'failed': failedCount};
  }

  /// Thực thi một thao tác cụ thể
  Future<bool> _executeAction(Map<String, dynamic> action) async {
    final endpoint = action['endpoint'] as String;
    final method = action['method'] as String;
    final payload = jsonDecode(action['payload'] as String) as Map<String, dynamic>;
    
    final url = Uri.parse('${ApiService.baseUrl}$endpoint');
    
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('auth_token');
    
    final headers = {
      'Content-Type': 'application/json',
      if (token != null) 'Authorization': 'Bearer $token',
    };

    http.Response response;
    
    switch (method.toUpperCase()) {
      case 'POST':
        response = await http.post(url, headers: headers, body: jsonEncode(payload))
            .timeout(const Duration(seconds: 15));
        break;
      case 'PUT':
        response = await http.put(url, headers: headers, body: jsonEncode(payload))
            .timeout(const Duration(seconds: 15));
        break;
      case 'DELETE':
        response = await http.delete(url, headers: headers)
            .timeout(const Duration(seconds: 15));
        break;
      default:
        return false;
    }

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      return data['success'] == true;
    }
    return false;
  }

  /// Đánh dấu đã hoàn thành
  Future<void> _markCompleted(int id) async {
    final db = await _appDatabase.database;
    await db.update(
      'offline_queue',
      {'status': 'completed'},
      where: 'id = ?',
      whereArgs: [id],
    );
  }

  /// Tăng số lần retry
  Future<void> _incrementRetry(int id, String error) async {
    final db = await _appDatabase.database;
    await db.rawUpdate(
      'UPDATE offline_queue SET retry_count = retry_count + 1, error_message = ? WHERE id = ?',
      [error, id],
    );

    // Kiểm tra nếu đã hết retry → đánh dấu failed
    final action = await db.query('offline_queue', where: 'id = ?', whereArgs: [id]);
    if (action.isNotEmpty) {
      final retryCount = action.first['retry_count'] as int? ?? 0;
      final maxRetries = action.first['max_retries'] as int? ?? 5;
      if (retryCount >= maxRetries) {
        await db.update(
          'offline_queue',
          {'status': 'failed'},
          where: 'id = ?',
          whereArgs: [id],
        );
        print('[QUEUE] Thao tác ID=$id đã thất bại sau $maxRetries lần thử.');
      }
    }
  }

  /// Xóa các thao tác đã hoàn thành (dọn dẹp)
  Future<int> cleanCompleted() async {
    final db = await _appDatabase.database;
    return await db.delete(
      'offline_queue',
      where: 'status = ?',
      whereArgs: ['completed'],
    );
  }

  /// Lấy thống kê hàng đợi
  Future<Map<String, int>> getQueueStats() async {
    final db = await _appDatabase.database;
    final pending = await db.rawQuery(
      "SELECT COUNT(*) as c FROM offline_queue WHERE status = 'pending'",
    );
    final completed = await db.rawQuery(
      "SELECT COUNT(*) as c FROM offline_queue WHERE status = 'completed'",
    );
    final failed = await db.rawQuery(
      "SELECT COUNT(*) as c FROM offline_queue WHERE status = 'failed'",
    );

    return {
      'pending': pending.first['c'] as int? ?? 0,
      'completed': completed.first['c'] as int? ?? 0,
      'failed': failed.first['c'] as int? ?? 0,
    };
  }
}
