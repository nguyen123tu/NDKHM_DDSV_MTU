import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/leave_request_model.dart';
import 'api_service.dart';
import 'package:shared_preferences/shared_preferences.dart';

class LeaveService {
  Future<Map<String, String>> _getHeaders() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('auth_token');
    return {
      'Content-Type': 'application/json',
      'ngrok-skip-browser-warning': '69420',
      if (token != null) 'Authorization': 'Bearer $token',
    };
  }

  /// Lấy danh sách lớp học
  Future<Map<String, dynamic>> getClasses() async {
    try {
      final response = await http.get(
        Uri.parse('${ApiService.baseUrl}/api/mobile/classes'),
        headers: await _getHeaders(),
      ).timeout(const Duration(seconds: 10));
      return jsonDecode(response.body);
    } catch (e) {
      return {'success': false, 'message': ApiService.friendlyError(e)};
    }
  }

  /// Sinh viên gửi đơn xin phép
  Future<Map<String, dynamic>> submitLeaveRequest(int lopId, String lyDo, String? imageBase64) async {
    try {
      final response = await http.post(
        Uri.parse('${ApiService.baseUrl}/api/mobile/leave-request'),
        headers: await _getHeaders(),
        body: jsonEncode({
          'lop_id': lopId,
          'ly_do': lyDo,
          'image_base64': imageBase64,
        }),
      ).timeout(const Duration(seconds: 15));
      return jsonDecode(response.body);
    } catch (e) {
      return {'success': false, 'message': ApiService.friendlyError(e)};
    }
  }

  /// Sinh viên lấy danh sách đơn của mình
  Future<Map<String, dynamic>> getMyLeaveRequests() async {
    try {
      final response = await http.get(
        Uri.parse('${ApiService.baseUrl}/api/mobile/my-leave-requests'),
        headers: await _getHeaders(),
      ).timeout(const Duration(seconds: 10));
      final data = jsonDecode(response.body);
      if (data['success'] == true) {
        List<LeaveRequest> list = (data['data'] as List).map((e) => LeaveRequest.fromJson(e)).toList();
        return {'success': true, 'data': list};
      }
      return data;
    } catch (e) {
      return {'success': false, 'message': ApiService.friendlyError(e)};
    }
  }

  /// Admin lấy danh sách tất cả đơn (có thể lọc theo status)
  Future<Map<String, dynamic>> getAdminLeaveRequests({int? status}) async {
    try {
      String url = '${ApiService.baseUrl}/api/mobile/admin/leave-requests';
      if (status != null) url += '?status=$status';
      
      final response = await http.get(
        Uri.parse(url),
        headers: await _getHeaders(),
      ).timeout(const Duration(seconds: 10));
      final data = jsonDecode(response.body);
      if (data['success'] == true) {
        List<LeaveRequest> list = (data['data'] as List).map((e) => LeaveRequest.fromJson(e)).toList();
        return {'success': true, 'data': list};
      }
      return data;
    } catch (e) {
      return {'success': false, 'message': ApiService.friendlyError(e)};
    }
  }

  /// Admin duyệt đơn
  Future<Map<String, dynamic>> approveLeaveRequest(int requestId) async {
    try {
      final response = await http.post(
        Uri.parse('${ApiService.baseUrl}/api/mobile/admin/approve-leave/$requestId'),
        headers: await _getHeaders(),
      ).timeout(const Duration(seconds: 10));
      return jsonDecode(response.body);
    } catch (e) {
      return {'success': false, 'message': ApiService.friendlyError(e)};
    }
  }

  /// Admin từ chối đơn
  Future<Map<String, dynamic>> rejectLeaveRequest(int requestId) async {
    try {
      final response = await http.post(
        Uri.parse('${ApiService.baseUrl}/api/mobile/admin/reject-leave/$requestId'),
        headers: await _getHeaders(),
      ).timeout(const Duration(seconds: 10));
      return jsonDecode(response.body);
    } catch (e) {
      return {'success': false, 'message': ApiService.friendlyError(e)};
    }
  }
}
