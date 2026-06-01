import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:uuid/uuid.dart';

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
  static const String baseUrl = 'http://172.16.3.91:5000';

  Future<Map<String, String>> _getHeaders() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('auth_token');
    return {
      'Content-Type': 'application/json',
      if (token != null) 'Authorization': 'Bearer $token',
    };
  }

  Future<String> _getDeviceId() async {
    final prefs = await SharedPreferences.getInstance();
    String? deviceId = prefs.getString('device_id');
    if (deviceId == null) {
      deviceId = const Uuid().v4();
      await prefs.setString('device_id', deviceId);
    }
    return deviceId;
  }

  Future<Map<String, dynamic>> login(String username, String password) async {
    final deviceId = await _getDeviceId();
    final response = await http.post(
      Uri.parse('$baseUrl/api/mobile/login'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'username': username,
        'password': password,
        'device_id': deviceId,
      }),
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

  Future<Map<String, dynamic>> getHistory(
      {int limit = 20, int? lopId, String? date, int? month, int? year}) async {
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

  Future<Map<String, dynamic>> recognizeFace(String base64Image,
      {double? lat, double? lng}) async {
    final headers = await _getHeaders();
    try {
      final response = await http
          .post(
            Uri.parse('$baseUrl/public/api/recognize'),
            headers: headers,
            body: jsonEncode({
              'image': base64Image,
              if (lat != null) 'lat': lat,
              if (lng != null) 'lng': lng,
            }),
          )
          .timeout(const Duration(seconds: 10));
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

  Future<Map<String, dynamic>> registerFace(
      String mssv, String hoTen, int lopId, List<String> imagesBase64) async {
    final headers = await _getHeaders();
    try {
      final response = await http
          .post(
            Uri.parse('$baseUrl/api/mobile/register_face'),
            headers: headers,
            body: jsonEncode({
              'mssv': mssv,
              'ho_ten': hoTen,
              'lop_id': lopId,
              'images': imagesBase64
            }),
          )
          .timeout(const Duration(seconds: 30));
      return jsonDecode(response.body);
    } catch (e) {
      return {'success': false, 'message': 'Lỗi kết nối: $e'};
    }
  }

  Future<Map<String, dynamic>> getProfile() async {
    final headers = await _getHeaders();
    final response = await http.get(Uri.parse('$baseUrl/api/mobile/profile'),
        headers: headers);
    return jsonDecode(response.body);
  }

  Future<Map<String, dynamic>> changePassword(
      String oldPassword, String newPassword) async {
    final headers = await _getHeaders();
    final response = await http.post(
      Uri.parse('$baseUrl/api/mobile/change-password'),
      headers: headers,
      body: jsonEncode(
          {'old_password': oldPassword, 'new_password': newPassword}),
    );
    return jsonDecode(response.body);
  }

  Future<Map<String, dynamic>> getSchedule() async {
    final headers = await _getHeaders();
    final response = await http.get(Uri.parse('$baseUrl/api/mobile/schedule'),
        headers: headers);
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
    final response = await http
        .get(Uri.parse('$baseUrl/api/mobile/pending-faces'), headers: headers);
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

  // ================================================================
  // PHIÊN ĐIỂM DANH (ATTENDANCE SESSIONS)
  // ================================================================

  /// Lấy danh sách phiên điểm danh đang mở
  Future<Map<String, dynamic>> getActiveSessions() async {
    final headers = await _getHeaders();
    final response = await http.get(
      Uri.parse('$baseUrl/api/mobile/sessions/active'),
      headers: headers,
    );
    return jsonDecode(response.body);
  }

  /// Admin tạo phiên điểm danh mới
  Future<Map<String, dynamic>> createSession(int lopId,
      {String moTa = '',
      int durationMinutes = 90,
      double? lat,
      double? lng}) async {
    final headers = await _getHeaders();
    final response = await http.post(
      Uri.parse('$baseUrl/api/mobile/sessions/create'),
      headers: headers,
      body: jsonEncode({
        'lop_id': lopId,
        'mo_ta': moTa,
        'duration_minutes': durationMinutes,
        'vi_do': lat,
        'kinh_do': lng,
      }),
    );
    return jsonDecode(response.body);
  }

  /// Admin đóng phiên điểm danh
  Future<Map<String, dynamic>> stopSession(int sessionId) async {
    final headers = await _getHeaders();
    final response = await http.post(
      Uri.parse('$baseUrl/api/mobile/sessions/$sessionId/stop'),
      headers: headers,
    );
    return jsonDecode(response.body);
  }

  /// Sinh viên tự điểm danh bằng khuôn mặt
  Future<Map<String, dynamic>> studentSelfCheckin(
      int sessionId, String imageBase64,
      {double? lat, double? lng}) async {
    final headers = await _getHeaders();
    try {
      final response = await http
          .post(
            Uri.parse('$baseUrl/api/mobile/student/checkin'),
            headers: headers,
            body: jsonEncode({
              'session_id': sessionId,
              'image_base64': imageBase64,
              'vi_do': lat,
              'kinh_do': lng,
            }),
          )
          .timeout(const Duration(seconds: 15));
      return jsonDecode(response.body);
    } catch (e) {
      return {'success': false, 'message': 'Lỗi kết nối: $e'};
    }
  }

  /// Admin lấy chi tiết phiên điểm danh (danh sách SV)
  Future<Map<String, dynamic>> getSessionDetails(int sessionId) async {
    final headers = await _getHeaders();
    final response = await http.get(
      Uri.parse('$baseUrl/api/mobile/sessions/$sessionId/details'),
      headers: headers,
    );
    return jsonDecode(response.body);
  }

  /// Admin lấy lịch sử phiên đã đóng
  Future<Map<String, dynamic>> getSessionHistory() async {
    final headers = await _getHeaders();
    final response = await http.get(
      Uri.parse('$baseUrl/api/mobile/sessions/history'),
      headers: headers,
    );
    return jsonDecode(response.body);
  }

  /// Admin xóa phiên điểm danh
  Future<Map<String, dynamic>> deleteSession(int sessionId) async {
    final headers = await _getHeaders();
    final response = await http.delete(
      Uri.parse('$baseUrl/api/mobile/sessions/$sessionId'),
      headers: headers,
    );
    return jsonDecode(response.body);
  }

  /// Admin xóa 1 bản ghi điểm danh
  Future<Map<String, dynamic>> deleteAttendanceRecord(int recordId) async {
    final headers = await _getHeaders();
    final response = await http.delete(
      Uri.parse('$baseUrl/api/mobile/attendance/$recordId'),
      headers: headers,
    );
    return jsonDecode(response.body);
  }

  /// Admin xóa toàn bộ lịch sử điểm danh
  Future<Map<String, dynamic>> clearAttendanceHistory() async {
    final headers = await _getHeaders();
    final response = await http.delete(
      Uri.parse('$baseUrl/api/mobile/attendance/clear'),
      headers: headers,
    );
    return jsonDecode(response.body);
  }

  // ================================================================
  // THỐNG KÊ (STATS)
  // ================================================================

  Future<Map<String, dynamic>> getStatsClasses() async {
    final headers = await _getHeaders();
    final response = await http.get(
      Uri.parse('$baseUrl/api/mobile/stats/classes'),
      headers: headers,
    );
    return jsonDecode(response.body);
  }

  Future<Map<String, dynamic>> getStatsAbsentRisk() async {
    final headers = await _getHeaders();
    final response = await http.get(
      Uri.parse('$baseUrl/api/mobile/stats/absent-risk'),
      headers: headers,
    );
    return jsonDecode(response.body);
  }

  Future<Map<String, dynamic>> getStatsDailyTrend() async {
    final headers = await _getHeaders();
    final response = await http.get(
      Uri.parse('$baseUrl/api/mobile/stats/daily-trend'),
      headers: headers,
    );
    return jsonDecode(response.body);
  }

  // ================================================================
  // THÔNG BÁO (NOTIFICATIONS)
  // ================================================================

  Future<Map<String, dynamic>> getNotifications() async {
    final headers = await _getHeaders();
    final response = await http.get(
      Uri.parse('$baseUrl/api/mobile/notifications'),
      headers: headers,
    );
    return jsonDecode(response.body);
  }

  Future<Map<String, dynamic>> markNotificationRead(int id) async {
    final headers = await _getHeaders();
    final response = await http.post(
      Uri.parse('$baseUrl/api/mobile/notifications/$id/read'),
      headers: headers,
    );
    return jsonDecode(response.body);
  }

  Future<Map<String, dynamic>> updateFcmToken(String fcmToken) async {
    final headers = await _getHeaders();
    final response = await http.post(
      Uri.parse('$baseUrl/api/mobile/fcm-token'),
      headers: headers,
      body: jsonEncode({'fcm_token': fcmToken}),
    );
    return jsonDecode(response.body);
  }

  // ================================================================
  // AI CHATBOT (Hỏi đáp AI)
  // ================================================================

  /// Gửi câu hỏi cho AI Chatbot
  Future<Map<String, dynamic>> askChatbot(String question) async {
    final headers = await _getHeaders();
    try {
      final response = await http
          .post(
            Uri.parse('$baseUrl/api/mobile/chatbot/ask'),
            headers: headers,
            body: jsonEncode({'question': question}),
          )
          .timeout(const Duration(seconds: 60));
      return jsonDecode(response.body);
    } catch (e) {
      return {'success': false, 'message': 'Lỗi kết nối hoặc quá thời gian: $e'};
    }
  }

  /// Lấy danh sách câu hỏi gợi ý
  Future<List<String>> getChatbotSuggestions() async {
    final headers = await _getHeaders();
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/api/mobile/chatbot/suggestions'),
        headers: headers,
      );
      final data = jsonDecode(response.body);
      if (data['success'] == true) {
        return List<String>.from(data['data']);
      }
    } catch (_) {}
    return [
      'Hệ thống điểm danh hoạt động như thế nào?',
      'Làm sao để train AI cho sinh viên mới?',
      'Cấu trúc database gồm những bảng nào?',
      'API mobile hỗ trợ những endpoint nào?',
    ];
  }

  /// Xóa lịch sử chat AI
  Future<Map<String, dynamic>> clearChatHistory() async {
    final headers = await _getHeaders();
    final response = await http.post(
      Uri.parse('$baseUrl/api/mobile/chatbot/clear'),
      headers: headers,
    );
    return jsonDecode(response.body);
  }
}
