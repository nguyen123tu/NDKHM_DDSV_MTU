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
      version: 2,
      onCreate: _createDB,
      onUpgrade: _upgradeDB,
    );
  }

  Future _createDB(Database db, int version) async {
    // ============================================================
    // BẢNG 1: Sinh viên (đồng bộ từ server)
    // ============================================================
    await db.execute('''
CREATE TABLE local_students (
  mssv TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  face_vector TEXT,
  lop_id INTEGER,
  updated_at TEXT
)
''');

    // ============================================================
    // BẢNG 2: Điểm danh offline (chờ đẩy lên server)
    // ============================================================
    await db.execute('''
CREATE TABLE local_attendance (
  local_uuid TEXT PRIMARY KEY,
  mssv TEXT NOT NULL,
  check_time TEXT NOT NULL,
  confidence REAL NOT NULL,
  session_id INTEGER,
  sync_status INTEGER NOT NULL DEFAULT 0
)
''');

    // ============================================================
    // BẢNG 3: Phiên điểm danh (cache từ server)
    // ============================================================
    await db.execute('''
CREATE TABLE local_sessions (
  id INTEGER PRIMARY KEY,
  lop_id INTEGER NOT NULL,
  ma_lop TEXT,
  ten_lop TEXT,
  giao_vien TEXT,
  mo_ta TEXT,
  bat_dau TEXT,
  het_han TEXT,
  trang_thai INTEGER DEFAULT 1,
  so_da_diem_danh INTEGER DEFAULT 0,
  tong_sv INTEGER DEFAULT 0,
  da_diem_danh_chua INTEGER DEFAULT 0,
  updated_at TEXT
)
''');

    // ============================================================
    // BẢNG 4: Lịch học (cache từ server)
    // ============================================================
    await db.execute('''
CREATE TABLE local_schedules (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  lop_id INTEGER,
  thu INTEGER,
  gio_bat_dau TEXT,
  gio_ket_thuc TEXT,
  phong TEXT,
  mon_hoc TEXT,
  giao_vien TEXT,
  ghi_chu TEXT,
  updated_at TEXT
)
''');

    // ============================================================
    // BẢNG 5: Thông báo (cache từ server)
    // ============================================================
    await db.execute('''
CREATE TABLE local_notifications (
  id INTEGER PRIMARY KEY,
  tieu_de TEXT,
  noi_dung TEXT,
  da_doc INTEGER DEFAULT 0,
  created_at TEXT
)
''');

    // ============================================================
    // BẢNG 6: Hàng đợi thao tác offline (Command Queue)
    // ============================================================
    await db.execute('''
CREATE TABLE offline_queue (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  local_uuid TEXT NOT NULL UNIQUE,
  action_type TEXT NOT NULL,
  endpoint TEXT NOT NULL,
  method TEXT NOT NULL DEFAULT 'POST',
  payload TEXT NOT NULL,
  created_at TEXT NOT NULL,
  retry_count INTEGER DEFAULT 0,
  max_retries INTEGER DEFAULT 5,
  status TEXT NOT NULL DEFAULT 'pending',
  error_message TEXT
)
''');

    // ============================================================
    // BẢNG 7: Metadata đồng bộ
    // ============================================================
    await db.execute('''
CREATE TABLE sync_metadata (
  data_type TEXT PRIMARY KEY,
  last_sync_time TEXT,
  last_sync_status TEXT,
  record_count INTEGER DEFAULT 0
)
''');

    // ============================================================
    // BẢNG 8: Cache dashboard stats
    // ============================================================
    await db.execute('''
CREATE TABLE cached_stats (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  updated_at TEXT NOT NULL
)
''');

    // ============================================================
    // BẢNG 9: Cache lịch sử điểm danh (hiển thị dashboard)
    // ============================================================
    await db.execute('''
CREATE TABLE cached_history (
  id INTEGER PRIMARY KEY,
  ho_ten TEXT,
  mssv TEXT,
  ma_lop TEXT,
  thoi_gian TEXT,
  gio_ra TEXT,
  trang_thai TEXT,
  avatar TEXT,
  evidence_path TEXT
)
''');
  }

  /// Migration từ version 1 lên version 2
  Future _upgradeDB(Database db, int oldVersion, int newVersion) async {
    if (oldVersion < 2) {
      // Thêm cột lop_id vào local_students nếu chưa có
      try {
        await db
            .execute('ALTER TABLE local_students ADD COLUMN lop_id INTEGER');
      } catch (_) {}

      // Thêm cột session_id vào local_attendance nếu chưa có
      try {
        await db.execute(
            'ALTER TABLE local_attendance ADD COLUMN session_id INTEGER');
      } catch (_) {}

      // Tạo các bảng mới
      await db.execute('''
CREATE TABLE IF NOT EXISTS local_sessions (
  id INTEGER PRIMARY KEY,
  lop_id INTEGER NOT NULL,
  ma_lop TEXT,
  ten_lop TEXT,
  giao_vien TEXT,
  mo_ta TEXT,
  bat_dau TEXT,
  het_han TEXT,
  trang_thai INTEGER DEFAULT 1,
  so_da_diem_danh INTEGER DEFAULT 0,
  tong_sv INTEGER DEFAULT 0,
  da_diem_danh_chua INTEGER DEFAULT 0,
  updated_at TEXT
)
''');

      await db.execute('''
CREATE TABLE IF NOT EXISTS local_schedules (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  lop_id INTEGER,
  thu INTEGER,
  gio_bat_dau TEXT,
  gio_ket_thuc TEXT,
  phong TEXT,
  mon_hoc TEXT,
  giao_vien TEXT,
  ghi_chu TEXT,
  updated_at TEXT
)
''');

      await db.execute('''
CREATE TABLE IF NOT EXISTS local_notifications (
  id INTEGER PRIMARY KEY,
  tieu_de TEXT,
  noi_dung TEXT,
  da_doc INTEGER DEFAULT 0,
  created_at TEXT
)
''');

      await db.execute('''
CREATE TABLE IF NOT EXISTS offline_queue (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  local_uuid TEXT NOT NULL UNIQUE,
  action_type TEXT NOT NULL,
  endpoint TEXT NOT NULL,
  method TEXT NOT NULL DEFAULT 'POST',
  payload TEXT NOT NULL,
  created_at TEXT NOT NULL,
  retry_count INTEGER DEFAULT 0,
  max_retries INTEGER DEFAULT 5,
  status TEXT NOT NULL DEFAULT 'pending',
  error_message TEXT
)
''');

      await db.execute('''
CREATE TABLE IF NOT EXISTS sync_metadata (
  data_type TEXT PRIMARY KEY,
  last_sync_time TEXT,
  last_sync_status TEXT,
  record_count INTEGER DEFAULT 0
)
''');

      await db.execute('''
CREATE TABLE IF NOT EXISTS cached_stats (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  updated_at TEXT NOT NULL
)
''');

      await db.execute('''
CREATE TABLE IF NOT EXISTS cached_history (
  id INTEGER PRIMARY KEY,
  ho_ten TEXT,
  mssv TEXT,
  ma_lop TEXT,
  thoi_gian TEXT,
  gio_ra TEXT,
  trang_thai TEXT,
  avatar TEXT,
  evidence_path TEXT
)
''');
    }
  }

  Future close() async {
    final db = await instance.database;
    db.close();
  }
}
