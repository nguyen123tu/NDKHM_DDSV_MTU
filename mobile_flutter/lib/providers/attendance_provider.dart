import 'package:flutter/material.dart';
import '../models/attendance_record.dart';
import '../services/api_service.dart';

class AttendanceProvider with ChangeNotifier {
  final ApiService _apiService = ApiService();
  
  DashboardStats? _stats;
  List<AttendanceRecord> _history = [];
  bool _isLoading = false;

  DashboardStats? get stats => _stats;
  List<AttendanceRecord> get history => _history;
  bool get isLoading => _isLoading;

  Future<void> fetchDashboardData() async {
    _isLoading = true;
    notifyListeners();

    try {
      final statsData = await _apiService.getDashboardStats();
      if (statsData['success'] == true) {
        _stats = DashboardStats.fromJson(statsData['data']);
      }

      final historyData = await _apiService.getHistory();
      if (historyData['success'] == true) {
        final List<dynamic> recordsRaw = historyData['data'];
        _history = recordsRaw.map((v) => AttendanceRecord.fromJson(v)).toList();
      }
    } catch (e) {
      debugPrint("Error fetching dashboard: $e");
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  // Luôn fetch lại history ngay sau khi quét mặt thành công
  Future<void> refreshHistory() async {
    await fetchDashboardData();
  }
}
