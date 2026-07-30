import '../local/app_database.dart';

/// Repository quản lý cache lịch học (sync từ server)
class ScheduleRepository {
  final AppDatabase _appDatabase = AppDatabase.instance;

  /// Lưu lịch học từ server (xóa cũ, thay mới)
  Future<void> replaceSchedules(List<dynamic> schedules) async {
    final db = await _appDatabase.database;

    // Xóa toàn bộ lịch cũ rồi thay mới
    await db.delete('local_schedules');

    final batch = db.batch();
    for (var s in schedules) {
      batch.insert('local_schedules', {
        'lop_id': s['lop_id'],
        'gio_bat_dau': s['gio_bat_dau'],
        'gio_ket_thuc': s['gio_ket_thuc'],
        'phong': s['phong'],
        'mon_hoc': s['mon_hoc'],
        'giao_vien': s['giao_vien'],
        'ghi_chu': s['ghi_chu'],
        'updated_at': DateTime.now().toIso8601String(),
      });
    }
    await batch.commit(noResult: true);
  }

  /// Lấy toàn bộ lịch học cached
  Future<List<Map<String, dynamic>>> getAllSchedules() async {
    final db = await _appDatabase.database;
    return await db.query(
      'local_schedules',
      orderBy: 'thu ASC, gio_bat_dau ASC',
    );
  }

  /// Xóa toàn bộ
  Future<void> clearAll() async {
    final db = await _appDatabase.database;
    await db.delete('local_schedules');
  }
}
