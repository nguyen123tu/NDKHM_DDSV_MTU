class UserModel {
  final String id;
  final String username;
  final String role;
  final String name;

  UserModel({
    required this.id,
    required this.username,
    required this.role,
    required this.name,
  });

  factory UserModel.fromJson(Map<String, dynamic> json) {
    return UserModel(
      id: json['id'].toString(),
      username: json['username'] ?? '',
      role: json['role'] ?? 'admin',
      name: json['name'] ?? '',
    );
  }
}
