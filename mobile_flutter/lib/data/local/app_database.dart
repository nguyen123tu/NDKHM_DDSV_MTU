import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';

class AppDatabase {
  static final AppDatabase instance = AppDatabase._init();
  static Database? _database;

  AppDatabase._init();

  Future<Database> get database async {
    if (_database != null) return _database!;
    _database = await _initDB('mtuface_offline.db');
    return _database!;
  }

  Future<Database> _initDB(String filePath) async {
    final dbPath = await getDatabasesPath();
    final path = join(dbPath, filePath);

    return await openDatabase(
      path,
      version: 1,
      onCreate: _createDB,
    );
  }

  Future _createDB(Database db, int version) async {
    const idType = 'TEXT PRIMARY KEY';
    const textType = 'TEXT NOT NULL';
    const textNullType = 'TEXT';
    const integerType = 'INTEGER NOT NULL';
    const realType = 'REAL NOT NULL';

    await db.execute('''
CREATE TABLE local_students (
  mssv $idType,
  name $textType,
  face_vector $textNullType,
  updated_at $textNullType
)
''');

    await db.execute('''
CREATE TABLE local_attendance (
  local_uuid $idType,
  mssv $textType,
  check_time $textType,
  confidence $realType,
  sync_status $integerType
)
''');
  }

  Future close() async {
    final db = await instance.database;
    db.close();
  }
}
