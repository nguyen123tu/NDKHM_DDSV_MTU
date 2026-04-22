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
  static const String baseUrl = 'http://127.0.0.1:5000';

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

  Future<Map<String, dynamic>> getHistory({int limit = 20}) async {
    final headers = await _getHeaders();
    final response = await http.get(
      Uri.parse('$baseUrl/api/mobile/history?limit=$limit'),
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
}
