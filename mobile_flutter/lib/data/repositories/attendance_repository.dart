import 'package:sqflite/sqflite.dart';
import 'package:uuid/uuid.dart';
import '../local/app_database.dart';

class AttendanceRepository {
  final AppDatabase _appDatabase = AppDatabase.instance;
  final _uuid = const Uuid();

  /// Ghi nhận điểm danh khi offline.
  /// Gọi hàm này lập tức sau khi quét thành công. App sẽ tự tạo UUID.
  Future<String> saveAttendanceOffline(String mssv, double confidence) async {
    final db = await _appDatabase.database;
    final localUuid = _uuid.v4(); // Tạo chuỗi chống trùng lặp duy nhất

    await db.insert(
      'local_attendance',
      {
        'local_uuid': localUuid,
        'mssv': mssv,
        'check_time': DateTime.now()
            .toIso8601String()
            .split('.')[0]
            .replaceFirst('T', ' '),
        'confidence': confidence,
        'sync_status': 0, // 0 = PENDING, chưa gửi lên server
      },
      conflictAlgorithm: ConflictAlgorithm.replace,
    );

    return localUuid;
  }

  /// Lấy toàn bộ log điểm danh chưa được đồng bộ
  Future<List<Map<String, dynamic>>> getPendingLogs() async {
    final db = await _appDatabase.database;
    return await db.query(
      'local_attendance',
      where: 'sync_status = ?',
      whereArgs: [0],
    );
  }

  /// Đánh dấu đã đồng bộ (cập nhật sync_status = 1 hoặc xóa log đi)
  Future<void> markAsSynced(List<String> localUuids) async {
    final db = await _appDatabase.database;
    final batch = db.batch();

    for (var uuid in localUuids) {
      // Cách 1: Đánh dấu thành 1
      // batch.update('local_attendance', {'sync_status': 1}, where: 'local_uuid = ?', whereArgs: [uuid]);

      // Cách 2: Xóa luôn khỏi điện thoại cho nhẹ máy (Khuyên dùng)
      batch.delete('local_attendance',
          where: 'local_uuid = ?', whereArgs: [uuid]);
    }

    await batch.commit(noResult: true);
  }
}
