import 'package:sqflite/sqflite.dart';
import '../local/app_database.dart';

/// Repository quản lý cache phiên điểm danh (sync từ server)
class SessionRepository {
  final AppDatabase _appDatabase = AppDatabase.instance;

  /// Lưu/cập nhật danh sách phiên điểm danh từ server
  Future<void> upsertSessions(List<dynamic> sessions) async {
    final db = await _appDatabase.database;
    final batch = db.batch();

    for (var session in sessions) {
      batch.insert(
        'local_sessions',
        {
          'id': session['id'],
          'lop_id': session['lop_id'],
          'ma_lop': session['ma_lop'],
          'ten_lop': session['ten_lop'],
          'giao_vien': session['giao_vien'],
          'mo_ta': session['mo_ta'],
          'bat_dau': session['bat_dau'],
          'het_han': session['het_han'],
          'trang_thai': session['trang_thai'] ?? 1,
          'so_da_diem_danh': session['so_da_diem_danh'] ?? 0,
          'tong_sv': session['tong_sv'] ?? 0,
          'da_diem_danh_chua': session['da_diem_danh_chua'] ?? 0,
          'updated_at': DateTime.now().toIso8601String(),
        },
        conflictAlgorithm: ConflictAlgorithm.replace,
      );
    }

    await batch.commit(noResult: true);
  }

  /// Lấy tất cả phiên đang mở (cached)
  Future<List<Map<String, dynamic>>> getActiveSessions() async {
    final db = await _appDatabase.database;
    return await db.query(
      'local_sessions',
      where: 'trang_thai = ?',
      whereArgs: [1],
      orderBy: 'bat_dau DESC',
    );
  }

  /// Lấy lịch sử phiên đã đóng (cached)
  Future<List<Map<String, dynamic>>> getSessionHistory() async {
    final db = await _appDatabase.database;
    return await db.query(
      'local_sessions',
      where: 'trang_thai = ?',
      whereArgs: [0],
      orderBy: 'bat_dau DESC',
      limit: 50,
    );
  }

  /// Xóa tất cả sessions cũ (dọn dẹp)
  Future<void> clearAll() async {
    final db = await _appDatabase.database;
    await db.delete('local_sessions');
  }
}
