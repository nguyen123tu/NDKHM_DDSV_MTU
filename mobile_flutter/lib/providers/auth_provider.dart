import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/user_model.dart';
import '../services/api_service.dart';

class AuthProvider with ChangeNotifier {
  final ApiService _apiService = ApiService();
  UserModel? _user;
  bool _isLoading = false;
  bool _hasSeenOnboarding = false;

  UserModel? get user => _user;
  bool get isLoading => _isLoading;
  bool get isAuthenticated => _user != null;
  bool get hasSeenOnboarding => _hasSeenOnboarding;

  Future<void> setOnboardingSeen() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('has_seen_onboarding', true);
    _hasSeenOnboarding = true;
    notifyListeners();
  }

  Future<void> checkAuthStatus() async {
    final prefs = await SharedPreferences.getInstance();
    
    _hasSeenOnboarding = prefs.getBool('has_seen_onboarding') ?? false;

    final token = prefs.getString('auth_token');
    if (token != null) {
      // In a real app we might fetch user via a /me endpoint, here we rely on saved prefs
      final username = prefs.getString('auth_username') ?? 'Admin';
      final name = prefs.getString('auth_name') ?? 'Admin';
      final role = prefs.getString('auth_role') ?? 'admin';
      _user = UserModel(id: '0', username: username, role: role, name: name);
    }
    notifyListeners();
  }

  Future<String?> login(String username, String password) async {
    _isLoading = true;
    notifyListeners();

    try {
      final data = await _apiService.login(username, password);
      if (data['success'] == true) {
        final prefs = await SharedPreferences.getInstance();
        await prefs.setString('auth_token', data['token']);
        
        final u = data['user'];
        await prefs.setString('auth_username', u['username']);
        await prefs.setString('auth_name', u['name'] ?? '');
        await prefs.setString('auth_role', u['role'] ?? 'admin');

        _user = UserModel.fromJson(u);
        _isLoading = false;
        notifyListeners();
        return null; // No error
      } else {
        _isLoading = false;
        notifyListeners();
        return data['message'] ?? 'Đăng nhập thất bại';
      }
    } catch (e) {
      _isLoading = false;
      notifyListeners();
      return 'Lỗi kết nối: ${e.toString()}';
    }
  }

  Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('auth_token');
    await prefs.remove('auth_username');
    await prefs.remove('auth_name');
    await prefs.remove('auth_role');
    _user = null;
    notifyListeners();
  }
}
