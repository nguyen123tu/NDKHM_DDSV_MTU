/// Model phiên điểm danh - do Admin tạo, Sinh viên tham gia
class AttendanceSession {
  final int id;
  final int lopId;
  final String maLop;
  final String tenLop;
  final String? giaoVien;
  final String? moTa;
  final String batDau;
  final String? hetHan;
  final int soDaDiemDanh;
  final int tongSv; // Tổng SV trong lớp (admin)
  final bool daDiemDanhChua; // Chỉ dành cho sinh viên

  AttendanceSession({
    required this.id,
    required this.lopId,
    required this.maLop,
    required this.tenLop,
    this.giaoVien,
    this.moTa,
    required this.batDau,
    this.hetHan,
    this.soDaDiemDanh = 0,
    this.tongSv = 0,
    this.daDiemDanhChua = false,
  });

  factory AttendanceSession.fromJson(Map<String, dynamic> json) {
    return AttendanceSession(
      id: json['id'] ?? 0,
      lopId: json['lop_id'] ?? 0,
      maLop: json['ma_lop'] ?? '',
      tenLop: json['ten_lop'] ?? '',
      giaoVien: json['giao_vien'],
      moTa: json['mo_ta'],
      batDau: json['bat_dau'] ?? '',
      hetHan: json['het_han'],
      soDaDiemDanh: json['so_da_diem_danh'] ?? 0,
      tongSv: json['tong_sv'] ?? 0,
      daDiemDanhChua: (json['da_diem_danh_chua'] ?? 0) > 0,
    );
  }

  /// Tính thời gian còn lại
  Duration? get thoiGianConLai {
    if (hetHan == null) return null;
    try {
      final expiry = DateTime.parse(hetHan!);
      final remaining = expiry.difference(DateTime.now());
      return remaining.isNegative ? Duration.zero : remaining;
    } catch (_) {
      return null;
    }
  }

  bool get isExpired {
    final remaining = thoiGianConLai;
    return remaining != null && remaining == Duration.zero;
  }
}
