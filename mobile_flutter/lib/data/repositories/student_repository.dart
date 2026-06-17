import 'package:sqflite/sqflite.dart';
import '../local/app_database.dart';

class StudentRepository {
  final AppDatabase _appDatabase = AppDatabase.instance;

  Future<void> insertOrUpdateStudent(Map<String, dynamic> student) async {
    final db = await _appDatabase.database;
    await db.insert(
      'local_students',
      {
        'mssv': student['student_id'] ?? student['mssv'],
        'name': student['name'] ?? student['ho_ten'],
        'face_vector': student['face_vector']?.toString(),
        'updated_at': student['updated_at'],
      },
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  Future<void> insertMultipleStudents(List<dynamic> students) async {
    final db = await _appDatabase.database;
    final batch = db.batch();

    for (var student in students) {
      // Nếu server đánh dấu đã xóa, ta xóa ở local
      if (student['is_deleted'] == true || student['trang_thai'] == 0) {
        batch.delete('local_students',
            where: 'mssv = ?',
            whereArgs: [student['student_id'] ?? student['mssv']]);
      } else {
        batch.insert(
          'local_students',
          {
            'mssv': student['student_id'] ?? student['mssv'],
            'name': student['name'] ?? student['ho_ten'],
            'face_vector': student['face_vector']?.toString(),
            'updated_at': student['updated_at'],
          },
          conflictAlgorithm: ConflictAlgorithm.replace,
        );
      }
    }

    await batch.commit(noResult: true);
  }

  Future<List<Map<String, dynamic>>> getAllStudentsOffline() async {
    final db = await _appDatabase.database;
    return await db.query('local_students');
  }

  Future<Map<String, dynamic>?> getStudentByMssv(String mssv) async {
    final db = await _appDatabase.database;
    final maps = await db.query(
      'local_students',
      where: 'mssv = ?',
      whereArgs: [mssv],
    );

    if (maps.isNotEmpty) {
      return maps.first;
    } else {
      return null;
    }
  }
}
