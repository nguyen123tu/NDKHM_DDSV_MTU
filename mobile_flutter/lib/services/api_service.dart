import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class ApiService {
  // ============================================================
  // CẤU HÌNH ĐỊA CHỈ SERVER
  // Chỉ cần thay đổi dòng baseUrl bên dưới tùy theo môi trường:
  //
  // 1. Chạy trên Chrome (Debug):
  //    static const String baseUrl = 'http://127.0.0.1:5000';
  //
  // 2. Chạy trên Android Emulator:
  //    static const String baseUrl = 'http://10.0.2.2:5000';
  //
  // 3. Chạy trên Điện Thoại Thật (cùng WiFi với máy tính):
  //    Mở CMD gõ "ipconfig", tìm dòng IPv4 Address (VD: 192.168.1.5)
  //    static const String baseUrl = 'http://192.168.1.5:5000';
  //
  // 4. Triển khai lên VPS/Cloud (Production):
  //    static const String baseUrl = 'https://your-domain.com';
  // ============================================================
  static const String baseUrl = 'http://192.168.1.67:5000';

  Future<Map<String, String>> _getHeaders() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('auth_token');
    return {
      'Content-Type': 'application/json',
      if (token != null) 'Authorization': 'Bearer $token',
    };
  }

  Future<Map<String, dynamic>> login(String username, String password) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/mobile/login'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'username': username, 'password': password}),
    );
    return jsonDecode(response.body);
  }

  Future<Map<String, dynamic>> getDashboardStats() async {
    final headers = await _getHeaders();
    final response = await http.get(
      Uri.parse('$baseUrl/api/mobile/stats'),
      headers: headers,
    );
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    throw Exception('Failed to load stats');
  }

  Future<Map<String, dynamic>> getHistory({int limit = 20, int? lopId, String? date, int? month, int? year}) async {
    final headers = await _getHeaders();
    String url = '$baseUrl/api/mobile/history?limit=$limit';
    if (lopId != null) url += '&lop_id=$lopId';
    if (date != null) url += '&date=$date';
    if (month != null) url += '&month=$month';
    if (year != null) url += '&year=$year';
    
    final response = await http.get(
      Uri.parse(url),
      headers: headers,
    );
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    throw Exception('Failed to load history');
  }

  Future<Map<String, dynamic>> recognizeFace(String base64Image) async {
    final headers = await _getHeaders();
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/public/api/recognize'),
        headers: headers,
        body: jsonEncode({'image': base64Image}),
      ).timeout(const Duration(seconds: 10));
      return jsonDecode(response.body);
    } catch (e) {
      return {'success': false, 'msg': 'Quá thời gian hoặc lỗi kết nối'};
    }
  }

  Future<List<dynamic>> getClasses() async {
    final response = await http.get(Uri.parse('$baseUrl/api/mobile/classes'));
    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      if (data['success'] == true) {
        return data['data'];
      }
    }
    throw Exception('Failed to load classes');
  }

  Future<Map<String, dynamic>> registerFace(String mssv, String hoTen, int lopId, List<String> imagesBase64) async {
    final headers = await _getHeaders();
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/api/mobile/register_face'),
        headers: headers,
        body: jsonEncode({
          'mssv': mssv,
          'ho_ten': hoTen,
          'lop_id': lopId,
          'images': imagesBase64
        }),
      ).timeout(const Duration(seconds: 30));
      return jsonDecode(response.body);
    } catch (e) {
      return {'success': false, 'message': 'Lỗi kết nối: $e'};
    }
  }

  Future<Map<String, dynamic>> getProfile() async {
    final headers = await _getHeaders();
    final response = await http.get(Uri.parse('$baseUrl/api/mobile/profile'), headers: headers);
    return jsonDecode(response.body);
  }

  Future<Map<String, dynamic>> changePassword(String oldPassword, String newPassword) async {
    final headers = await _getHeaders();
    final response = await http.post(
      Uri.parse('$baseUrl/api/mobile/change-password'),
      headers: headers,
      body: jsonEncode({'old_password': oldPassword, 'new_password': newPassword}),
    );
    return jsonDecode(response.body);
  }

  Future<Map<String, dynamic>> getSchedule() async {
    final headers = await _getHeaders();
    final response = await http.get(Uri.parse('$baseUrl/api/mobile/schedule'), headers: headers);
    return jsonDecode(response.body);
  }

  Future<Map<String, dynamic>> updateAvatar(String base64Image) async {
    final headers = await _getHeaders();
    final response = await http.post(
      Uri.parse('$baseUrl/api/mobile/update-avatar'),
      headers: headers,
      body: jsonEncode({'image': base64Image}),
    );
    return jsonDecode(response.body);
  }

  Future<Map<String, dynamic>> updateProfile(Map<String, dynamic> data) async {
    final headers = await _getHeaders();
    final response = await http.post(
      Uri.parse('$baseUrl/api/mobile/update-profile'),
      headers: headers,
      body: jsonEncode(data),
    );
    return jsonDecode(response.body);
  }

  Future<Map<String, dynamic>> getFaceGallery({String? mssv}) async {
    final headers = await _getHeaders();
    String url = '$baseUrl/api/mobile/face-gallery';
    if (mssv != null) url += '?mssv=$mssv';
    final response = await http.get(Uri.parse(url), headers: headers);
    return jsonDecode(response.body);
  }

  Future<Map<String, dynamic>> getPendingFaces() async {
    final headers = await _getHeaders();
    final response = await http.get(Uri.parse('$baseUrl/api/mobile/pending-faces'), headers: headers);
    return jsonDecode(response.body);
  }

  Future<Map<String, dynamic>> approveFace(int svId, int status) async {
    final headers = await _getHeaders();
    final response = await http.post(
      Uri.parse('$baseUrl/api/mobile/approve-face'),
      headers: headers,
      body: jsonEncode({'id': svId, 'status': status}),
    );
    return jsonDecode(response.body);
  }
}
