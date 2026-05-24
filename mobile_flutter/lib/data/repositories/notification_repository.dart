import 'package:sqflite/sqflite.dart';
import '../local/app_database.dart';

/// Repository quản lý cache thông báo (sync từ server)
class NotificationRepository {
  final AppDatabase _appDatabase = AppDatabase.instance;

  /// Lưu/cập nhật thông báo từ server
  Future<void> upsertNotifications(List<dynamic> notifications) async {
    final db = await _appDatabase.database;
    final batch = db.batch();

    for (var noti in notifications) {
      batch.insert(
        'local_notifications',
        {
          'id': noti['id'],
          'tieu_de': noti['tieu_de'],
          'noi_dung': noti['noi_dung'],
          'da_doc': noti['da_doc'] ?? 0,
          'created_at': noti['created_at']?.toString(),
        },
        conflictAlgorithm: ConflictAlgorithm.replace,
      );
    }

    await batch.commit(noResult: true);
  }

  /// Lấy toàn bộ thông báo cached
  Future<List<Map<String, dynamic>>> getAllNotifications() async {
    final db = await _appDatabase.database;
    return await db.query(
      'local_notifications',
      orderBy: 'created_at DESC',
      limit: 50,
    );
  }

  /// Đánh dấu đã đọc (local)
  Future<void> markAsRead(int id) async {
    final db = await _appDatabase.database;
    await db.update(
      'local_notifications',
      {'da_doc': 1},
      where: 'id = ?',
      whereArgs: [id],
    );
  }

  /// Đếm chưa đọc
  Future<int> getUnreadCount() async {
    final db = await _appDatabase.database;
    final result = await db.rawQuery(
      'SELECT COUNT(*) as c FROM local_notifications WHERE da_doc = 0',
    );
    return result.first['c'] as int? ?? 0;
  }

  /// Xóa toàn bộ
  Future<void> clearAll() async {
    final db = await _appDatabase.database;
    await db.delete('local_notifications');
  }
}
