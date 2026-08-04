class UserModel {
  final String id;
  final String username;
  final String role;
  final String name;
  final String? mssv; // MSSV cho sinh viên
  final String? lopName;

  UserModel({
    required this.id,
    required this.username,
    required this.role,
    required this.name,
    this.mssv,
    this.lopName,
  });

  factory UserModel.fromJson(Map<String, dynamic> json) {
    return UserModel(
      id: json['id'].toString(),
      username: json['username'] ?? '',
      role: json['role'] ?? 'admin',
      name: json['name'] ?? '',
      mssv: json['role'] == 'student' ? (json['username'] ?? '') : null,
      lopName: json['ten_lop'],
    );
  }
}
