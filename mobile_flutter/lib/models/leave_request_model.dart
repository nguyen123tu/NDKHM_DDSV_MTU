class LeaveRequest {
  final int id;
  final String lyDo;
  final String? minhChungUrl;
  final int trangThai; // 0: Đang chờ, 1: Đã duyệt, 2: Từ chối
  final String? thoiGianTao;
  final String? tenLop;
  final String? maLop;
  final String? hoTen;
  final String? mssv;
  final int? sinhVienId;

  LeaveRequest({
    required this.id,
    required this.lyDo,
    this.minhChungUrl,
    required this.trangThai,
    this.thoiGianTao,
    this.tenLop,
    this.maLop,
    this.hoTen,
    this.mssv,
    this.sinhVienId,
  });

  factory LeaveRequest.fromJson(Map<String, dynamic> json) {
    return LeaveRequest(
      id: json['id'],
      lyDo: json['ly_do'] ?? '',
      minhChungUrl: json['minh_chung_url'],
      trangThai: json['trang_thai'] ?? 0,
      thoiGianTao: json['thoi_gian_tao'],
      tenLop: json['ten_lop'],
      maLop: json['ma_lop'],
      hoTen: json['ho_ten'],
      mssv: json['mssv'],
      sinhVienId: json['sinh_vien_id'],
    );
  }
}
