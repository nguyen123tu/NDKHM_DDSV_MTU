import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:uuid/uuid.dart';

class ApiService {
  // ============================================================
  // CẤU HÌNH ĐỊA CHỈ SERVER
  // URL mặc định — có thể thay đổi từ trong App (Cài đặt Server)
  // ============================================================
  static const String _defaultBaseUrl =
      'https://swathable-untangentially-hadlee.ngrok-free.dev';

  /// Cache URL trong bộ nhớ để tránh đọc SharedPreferences mỗi lần gọi API
  static String? _cachedBaseUrl;

  /// Lấy baseUrl hiện tại (ưu tiên URL tùy chỉnh trong SharedPreferences)
  static String get baseUrl => _cachedBaseUrl ?? _defaultBaseUrl;

  /// Khởi tạo baseUrl từ SharedPreferences (gọi 1 lần khi app khởi động)
  static Future<void> initBaseUrl() async {
    final prefs = await SharedPreferences.getInstance();
    _cachedBaseUrl = prefs.getString('custom_server_url') ?? _defaultBaseUrl;
  }

  /// Lưu URL server tùy chỉnh
  static Future<void> setServerUrl(String url) async {
    final prefs = await SharedPreferences.getInstance();
    // Xóa khoảng trắng, bỏ / cuối
    url = url.trim().replaceAll(RegExp(r'/+$'), '');
    if (url.isEmpty) url = _defaultBaseUrl;
    await prefs.setString('custom_server_url', url);
    _cachedBaseUrl = url;
  }

  /// Lấy URL server tùy chỉnh (hoặc mặc định)
  static Future<String> getServerUrl() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('custom_server_url') ?? _defaultBaseUrl;
  }

  /// Đặt lại về URL mặc định
  static Future<void> resetServerUrl() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('custom_server_url');
    _cachedBaseUrl = _defaultBaseUrl;
  }

  /// Chuyển đổi lỗi kỹ thuật thành thông báo thân thiện cho người dùng
  static String friendlyError(dynamic e) {
    final msg = e.toString().toLowerCase();
    if (msg.contains('timeout') || msg.contains('timed out')) {
      return 'Máy chủ không phản hồi. Vui lòng kiểm tra kết nối mạng và thử lại.';
    }
    if (msg.contains('socketexception') || msg.contains('connection refused')) {
      return 'Không thể kết nối tới máy chủ. Hãy chắc chắn server đang chạy.';
    }
    if (msg.contains('handshake') || msg.contains('certificate')) {
      return 'Lỗi bảo mật kết nối (SSL). Vui lòng kiểm tra địa chỉ server.';
    }
    if (msg.contains('connection reset') || msg.contains('connection closed')) {
      return 'Kết nối bị ngắt giữa chừng. Vui lòng thử lại.';
    }
    if (msg.contains('no internet') || msg.contains('network is unreachable')) {
      return 'Không có kết nối Internet. Hãy kiểm tra WiFi/4G.';
    }
    if (msg.contains('formatexception') ||
        msg.contains('unexpected character')) {
      return 'Máy chủ trả về dữ liệu không hợp lệ. Liên hệ Admin.';
    }
    // Trả về lỗi gốc nếu không match
    return 'Lỗi: ${e.toString().replaceAll('Exception: ', '').replaceAll('TimeoutException after', 'Quá thời gian sau')}';
  }

  Future<Map<String, String>> _getHeaders() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('auth_token');
    return {
      'Content-Type': 'application/json',
      'ngrok-skip-browser-warning': '69420',
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
    try {
      final response = await http
          .post(
            Uri.parse('$baseUrl/api/mobile/login'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({
              'username': username,
              'password': password,
              'device_id': deviceId,
            }),
          )
          .timeout(const Duration(seconds: 10));
      return jsonDecode(response.body);
    } catch (e) {
      return {'success': false, 'message': 'Lỗi kết nối: $e'};
    }
  }

  Future<Map<String, dynamic>> getDashboardStats() async {
    final headers = await _getHeaders();
    try {
      final response = await http
          .get(
            Uri.parse('$baseUrl/api/mobile/stats'),
            headers: headers,
          )
          .timeout(const Duration(seconds: 10));
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      }
      return {
        'success': false,
        'message': 'Server error: ${response.statusCode}'
      };
    } catch (e) {
      return {'success': false, 'message': 'Lỗi kết nối: $e'};
    }
  }

  Future<Map<String, dynamic>> getHistory(
      {int limit = 20, int? lopId, String? date, int? month, int? year}) async {
    final headers = await _getHeaders();
    String url = '$baseUrl/api/mobile/history?limit=$limit';
    if (lopId != null) url += '&lop_id=$lopId';
    if (date != null) url += '&date=$date';
    if (month != null) url += '&month=$month';
    if (year != null) url += '&year=$year';

    try {
      final response = await http
          .get(
            Uri.parse(url),
            headers: headers,
          )
          .timeout(const Duration(seconds: 10));
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      }
      return {
        'success': false,
        'message': 'Server error: ${response.statusCode}'
      };
    } catch (e) {
      return {'success': false, 'message': 'Lỗi kết nối: $e'};
    }
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
    final headers = await _getHeaders();
    try {
      final response = await http
          .get(
            Uri.parse('$baseUrl/api/mobile/classes'),
            headers: headers,
          )
          .timeout(const Duration(seconds: 10));
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['success'] == true) {
          return data['data'];
        }
      }
    } catch (_) {}
    return [];
  }

  Future<Map<String, dynamic>> registerFace(
      String mssv, String hoTen, int lopId, List<String> imagesBase64,
      {String? email, String? sdt, String? ngaySinh, int? gioiTinh}) async {
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
              'email': email,
              'sdt': sdt,
              'ngay_sinh': ngaySinh,
              'gioi_tinh': gioiTinh,
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
    try {
      final response = await http
          .get(Uri.parse('$baseUrl/api/mobile/profile'), headers: headers)
          .timeout(const Duration(seconds: 10));
      return jsonDecode(response.body);
    } catch (e) {
      return {'success': false, 'message': 'Lỗi kết nối: $e'};
    }
  }

  Future<Map<String, dynamic>> changePassword(
      String oldPassword, String newPassword) async {
    final headers = await _getHeaders();
    try {
      final response = await http
          .post(
            Uri.parse('$baseUrl/api/mobile/change-password'),
            headers: headers,
            body: jsonEncode(
                {'old_password': oldPassword, 'new_password': newPassword}),
          )
          .timeout(const Duration(seconds: 10));
      return jsonDecode(response.body);
    } catch (e) {
      return {'success': false, 'message': 'Lỗi kết nối: $e'};
    }
  }

  Future<Map<String, dynamic>> getSchedule() async {
    final headers = await _getHeaders();
    try {
      final response = await http
          .get(Uri.parse('$baseUrl/api/mobile/schedule'), headers: headers)
          .timeout(const Duration(seconds: 10));
      return jsonDecode(response.body);
    } catch (e) {
      return {'success': false, 'message': 'Lỗi kết nối: $e'};
    }
  }

  Future<Map<String, dynamic>> updateAvatar(String base64Image) async {
    final headers = await _getHeaders();
    try {
      final response = await http
          .post(
            Uri.parse('$baseUrl/api/mobile/update-avatar'),
            headers: headers,
            body: jsonEncode({'image': base64Image}),
          )
          .timeout(const Duration(seconds: 15));
      return jsonDecode(response.body);
    } catch (e) {
      return {'success': false, 'message': 'Lỗi kết nối: $e'};
    }
  }

  Future<Map<String, dynamic>> updateProfile(Map<String, dynamic> data) async {
    final headers = await _getHeaders();
    try {
      final response = await http
          .post(
            Uri.parse('$baseUrl/api/mobile/update-profile'),
            headers: headers,
            body: jsonEncode(data),
          )
          .timeout(const Duration(seconds: 10));
      return jsonDecode(response.body);
    } catch (e) {
      return {'success': false, 'message': 'Lỗi kết nối: $e'};
    }
  }

  Future<Map<String, dynamic>> getFaceGallery({String? mssv}) async {
    final headers = await _getHeaders();
    String url = '$baseUrl/api/mobile/face-gallery';
    if (mssv != null) url += '?mssv=$mssv';
    try {
      final response = await http
          .get(Uri.parse(url), headers: headers)
          .timeout(const Duration(seconds: 10));
      return jsonDecode(response.body);
    } catch (e) {
      return {'success': false, 'message': 'Lỗi kết nối: $e'};
    }
  }

  Future<Map<String, dynamic>> getPendingFaces() async {
    final headers = await _getHeaders();
    try {
      final response = await http
          .get(Uri.parse('$baseUrl/api/mobile/pending-faces'), headers: headers)
          .timeout(const Duration(seconds: 10));
      return jsonDecode(response.body);
    } catch (e) {
      return {'success': false, 'message': 'Lỗi kết nối: $e'};
    }
  }

  Future<Map<String, dynamic>> approveFace(int svId, int status) async {
    final headers = await _getHeaders();
    try {
      final response = await http
          .post(
            Uri.parse('$baseUrl/api/mobile/approve-face'),
            headers: headers,
            body: jsonEncode({'id': svId, 'status': status}),
          )
          .timeout(const Duration(seconds: 10));
      return jsonDecode(response.body);
    } catch (e) {
      return {'success': false, 'message': 'Lỗi kết nối: $e'};
    }
  }

  // ================================================================
  // PHIÊN ĐIỂM DANH (ATTENDANCE SESSIONS)
  // ================================================================

  /// Lấy danh sách phiên điểm danh đang mở
  Future<Map<String, dynamic>> getActiveSessions() async {
    final headers = await _getHeaders();
    try {
      final response = await http
          .get(
            Uri.parse('$baseUrl/api/mobile/sessions/active'),
            headers: headers,
          )
          .timeout(const Duration(seconds: 10));
      return jsonDecode(response.body);
    } catch (e) {
      return {'success': false, 'message': 'Lỗi kết nối: $e'};
    }
  }

  /// Admin tạo phiên điểm danh mới
  Future<Map<String, dynamic>> createSession(int lopId,
      {String moTa = '',
      int durationMinutes = 90,
      double? lat,
      double? lng}) async {
    final headers = await _getHeaders();
    try {
      final response = await http
          .post(
            Uri.parse('$baseUrl/api/mobile/sessions/create'),
            headers: headers,
            body: jsonEncode({
              'lop_id': lopId,
              'mo_ta': moTa,
              'duration_minutes': durationMinutes,
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

  /// Admin đóng phiên điểm danh
  Future<Map<String, dynamic>> stopSession(int sessionId) async {
    final headers = await _getHeaders();
    try {
      final response = await http
          .post(
            Uri.parse('$baseUrl/api/mobile/sessions/$sessionId/stop'),
            headers: headers,
          )
          .timeout(const Duration(seconds: 10));
      return jsonDecode(response.body);
    } catch (e) {
      return {'success': false, 'message': 'Lỗi kết nối: $e'};
    }
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
    try {
      final response = await http
          .get(
            Uri.parse('$baseUrl/api/mobile/sessions/$sessionId/details'),
            headers: headers,
          )
          .timeout(const Duration(seconds: 10));
      return jsonDecode(response.body);
    } catch (e) {
      return {'success': false, 'message': 'Lỗi kết nối: $e'};
    }
  }

  /// Admin lấy lịch sử phiên đã đóng
  Future<Map<String, dynamic>> getSessionHistory() async {
    final headers = await _getHeaders();
    try {
      final response = await http
          .get(
            Uri.parse('$baseUrl/api/mobile/sessions/history'),
            headers: headers,
          )
          .timeout(const Duration(seconds: 10));
      return jsonDecode(response.body);
    } catch (e) {
      return {'success': false, 'message': 'Lỗi kết nối: $e'};
    }
  }

  Future<Map<String, dynamic>> deleteSession(int sessionId) async {
    final headers = await _getHeaders();
    try {
      final response = await http
          .delete(
            Uri.parse('$baseUrl/api/mobile/sessions/$sessionId'),
            headers: headers,
          )
          .timeout(const Duration(seconds: 10));
      return jsonDecode(response.body);
    } catch (e) {
      return {'success': false, 'message': 'Lỗi kết nối: $e'};
    }
  }

  Future<Map<String, dynamic>> deleteAttendanceRecord(int recordId) async {
    final headers = await _getHeaders();
    try {
      final response = await http
          .delete(
            Uri.parse('$baseUrl/api/mobile/attendance/$recordId'),
            headers: headers,
          )
          .timeout(const Duration(seconds: 10));
      return jsonDecode(response.body);
    } catch (e) {
      return {'success': false, 'message': 'Lỗi kết nối: $e'};
    }
  }

  /// Admin xóa toàn bộ lịch sử điểm danh
  Future<Map<String, dynamic>> clearAttendanceHistory() async {
    final headers = await _getHeaders();
    try {
      final response = await http
          .delete(
            Uri.parse('$baseUrl/api/mobile/attendance/clear'),
            headers: headers,
          )
          .timeout(const Duration(seconds: 10));
      return jsonDecode(response.body);
    } catch (e) {
      return {'success': false, 'message': 'Lỗi kết nối: $e'};
    }
  }

  // ================================================================
  // THỐNG KÊ (STATS)
  // ================================================================

  Future<Map<String, dynamic>> getStatsClasses() async {
    final headers = await _getHeaders();
    try {
      final response = await http
          .get(
            Uri.parse('$baseUrl/api/mobile/stats/classes'),
            headers: headers,
          )
          .timeout(const Duration(seconds: 10));
      return jsonDecode(response.body);
    } catch (e) {
      return {'success': false, 'message': 'Lỗi kết nối: $e'};
    }
  }

  Future<Map<String, dynamic>> getStatsAbsentRisk() async {
    final headers = await _getHeaders();
    try {
      final response = await http
          .get(
            Uri.parse('$baseUrl/api/mobile/stats/absent-risk'),
            headers: headers,
          )
          .timeout(const Duration(seconds: 10));
      return jsonDecode(response.body);
    } catch (e) {
      return {'success': false, 'message': 'Lỗi kết nối: $e'};
    }
  }

  Future<Map<String, dynamic>> getStatsDailyTrend() async {
    final headers = await _getHeaders();
    try {
      final response = await http
          .get(
            Uri.parse('$baseUrl/api/mobile/stats/daily-trend'),
            headers: headers,
          )
          .timeout(const Duration(seconds: 10));
      return jsonDecode(response.body);
    } catch (e) {
      return {'success': false, 'message': 'Lỗi kết nối: $e'};
    }
  }

  // ================================================================
  // THÔNG BÁO (NOTIFICATIONS)
  // ================================================================

  Future<Map<String, dynamic>> getNotifications() async {
    final headers = await _getHeaders();
    try {
      final response = await http
          .get(
            Uri.parse('$baseUrl/api/mobile/notifications'),
            headers: headers,
          )
          .timeout(const Duration(seconds: 10));
      return jsonDecode(response.body);
    } catch (e) {
      return {'success': false, 'message': 'Lỗi kết nối: $e'};
    }
  }

  Future<Map<String, dynamic>> markNotificationRead(int id) async {
    final headers = await _getHeaders();
    try {
      final response = await http
          .post(
            Uri.parse('$baseUrl/api/mobile/notifications/$id/read'),
            headers: headers,
          )
          .timeout(const Duration(seconds: 10));
      return jsonDecode(response.body);
    } catch (e) {
      return {'success': false, 'message': 'Lỗi kết nối: $e'};
    }
  }

  Future<Map<String, dynamic>> markAllNotificationsRead() async {
    final headers = await _getHeaders();
    try {
      final response = await http
          .post(
            Uri.parse('$baseUrl/api/mobile/notifications/read-all'),
            headers: headers,
          )
          .timeout(const Duration(seconds: 10));
      return jsonDecode(response.body);
    } catch (e) {
      return {'success': false, 'message': 'Lỗi kết nối: $e'};
    }
  }

  Future<Map<String, dynamic>> updateFcmToken(String fcmToken) async {
    final headers = await _getHeaders();
    try {
      final response = await http
          .post(
            Uri.parse('$baseUrl/api/mobile/fcm-token'),
            headers: headers,
            body: jsonEncode({'fcm_token': fcmToken}),
          )
          .timeout(const Duration(seconds: 10));
      return jsonDecode(response.body);
    } catch (e) {
      return {'success': false, 'message': 'Lỗi kết nối: $e'};
    }
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
          .timeout(const Duration(seconds: 120));
      return jsonDecode(response.body);
    } catch (e) {
      return {
        'success': false,
        'message': 'Lỗi kết nối hoặc quá thời gian: $e'
      };
    }
  }

  /// Lấy danh sách câu hỏi gợi ý
  Future<List<String>> getChatbotSuggestions() async {
    final headers = await _getHeaders();
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/chatbot/suggestions'),
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
    try {
      final response = await http
          .post(
            Uri.parse('$baseUrl/chatbot/clear'),
            headers: headers,
          )
          .timeout(const Duration(seconds: 10));
      return jsonDecode(response.body);
    } catch (e) {
      return {'success': false, 'message': 'Lỗi kết nối: $e'};
    }
  }

  // ================================================================
  // QUẢN LÝ SINH VIÊN (ADMIN)
  // ================================================================

  Future<Map<String, dynamic>> getAdminStudents({String query = ''}) async {
    final headers = await _getHeaders();
    try {
      final response = await http
          .get(
            Uri.parse('$baseUrl/api/mobile/admin/students?q=$query'),
            headers: headers,
          )
          .timeout(const Duration(seconds: 15));
      return jsonDecode(response.body);
    } catch (e) {
      return {'success': false, 'message': 'Lỗi kết nối: $e'};
    }
  }

  Future<Map<String, dynamic>> updateStudent(
      int id, Map<String, dynamic> data) async {
    final headers = await _getHeaders();
    try {
      final response = await http
          .put(
            Uri.parse('$baseUrl/api/mobile/admin/students/$id'),
            headers: headers,
            body: jsonEncode(data),
          )
          .timeout(const Duration(seconds: 15));
      return jsonDecode(response.body);
    } catch (e) {
      return {'success': false, 'message': 'Lỗi kết nối: $e'};
    }
  }

  Future<Map<String, dynamic>> deleteStudent(int id) async {
    final headers = await _getHeaders();
    try {
      final response = await http
          .delete(
            Uri.parse('$baseUrl/api/mobile/admin/students/$id'),
            headers: headers,
          )
          .timeout(const Duration(seconds: 15));
      return jsonDecode(response.body);
    } catch (e) {
      return {'success': false, 'message': 'Lỗi kết nối: $e'};
    }
  }

  Future<Map<String, dynamic>> resetStudentFace(int id) async {
    final headers = await _getHeaders();
    try {
      final response = await http
          .post(
            Uri.parse('$baseUrl/api/mobile/admin/students/$id/reset-face'),
            headers: headers,
          )
          .timeout(const Duration(seconds: 15));
      return jsonDecode(response.body);
    } catch (e) {
      return {'success': false, 'message': 'Lỗi kết nối: $e'};
    }
  }
}
