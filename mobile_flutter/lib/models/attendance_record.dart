class AttendanceRecord {
  final String thoiGian;
  final String? gioRa;
  final String trangThai;
  final String hoTen;
  final String mssv;
  final String maLop;
  final String? avatar;
  final String? evidencePath;

  AttendanceRecord({
    required this.thoiGian,
    this.gioRa,
    required this.trangThai,
    required this.hoTen,
    required this.mssv,
    required this.maLop,
    this.avatar,
    this.evidencePath,
  });

  factory AttendanceRecord.fromJson(Map<String, dynamic> json) {
    return AttendanceRecord(
      thoiGian: json['thoi_gian'] ?? '',
      gioRa: json['gio_ra'],
      trangThai: json['trang_thai'] ?? 'Unknown',
      hoTen: json['ho_ten'] ?? 'Unknown',
      mssv: json['mssv'] ?? '',
      maLop: json['ma_lop'] ?? '',
      avatar: json['avatar'],
      evidencePath: json['evidence_path'],
    );
  }
}

class DashboardStats {
  final int total;
  final int present;
  final int absent;

  DashboardStats({required this.total, required this.present, required this.absent});

  factory DashboardStats.fromJson(Map<String, dynamic> json) {
    return DashboardStats(
      total: json['total'] ?? 0,
      present: json['present'] ?? 0,
      absent: json['absent'] ?? 0,
    );
  }
}
