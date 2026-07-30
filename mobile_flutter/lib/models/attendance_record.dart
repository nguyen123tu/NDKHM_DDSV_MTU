class AttendanceRecord {
  final int? id;
  final String thoiGian;
  final String? gioRa;
  final String trangThai;
  final String hoTen;
  final String mssv;
  final String maLop;
  final String? avatar;
  final String? evidencePath;

  AttendanceRecord({
    this.id,
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
      id: json['id'],
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
  final int late;
  final double rate;

  DashboardStats({
    required this.total,
    required this.present,
    required this.absent,
    this.late = 0,
    this.rate = 0.0,
  });

  factory DashboardStats.fromJson(Map<String, dynamic> json) {
    return DashboardStats(
      total: json['total'] ?? 0,
      present: json['present'] ?? 0,
      absent: json['absent'] ?? 0,
      late: json['late'] ?? 0,
      rate: (json['rate'] ?? 0.0).toDouble(),
    );
  }
}
