import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:crypto/crypto.dart' show sha256;
import '../models/user_model.dart';
import '../services/api_service.dart';
import '../services/firebase_messaging_service.dart';
import 'package:flutter/foundation.dart';

class AuthProvider with ChangeNotifier {
  final ApiService _apiService = ApiService();
  UserModel? _user;
  bool _isLoading = false;
  bool _hasSeenOnboarding = false;
  bool _isOfflineMode = false;

  UserModel? get user => _user;
  bool get isLoading => _isLoading;
  bool get isAuthenticated => _user != null;
  bool get hasSeenOnboarding => _hasSeenOnboarding;
  bool get isOfflineMode => _isOfflineMode;

  Future<void> setOnboardingSeen() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('has_seen_onboarding', true);
    _hasSeenOnboarding = true;
    notifyListeners();
  }

  Future<void> checkAuthStatus() async {
    final prefs = await SharedPreferences.getInstance();
    _hasSeenOnboarding = prefs.getBool('has_seen_onboarding') ?? false;

    final useBiometric = prefs.getBool('use_biometric') ??
        true; // Default to true to force login screen

    final token = prefs.getString('auth_token');
    if (token != null && !useBiometric) {
      // Auto login only if biometric is NOT enabled
      final username = prefs.getString('auth_username') ?? 'Admin';
      final name = prefs.getString('auth_name') ?? 'Admin';
      final role = prefs.getString('auth_role') ?? 'admin';
      _user = UserModel(id: '0', username: username, role: role, name: name);
    }
    notifyListeners();
  }

  Future<bool> loginWithCachedToken() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('auth_token');
    if (token != null) {
      final username = prefs.getString('auth_username') ?? 'Admin';
      final name = prefs.getString('auth_name') ?? 'Admin';
      final role = prefs.getString('auth_role') ?? 'admin';
      _user = UserModel(id: '0', username: username, role: role, name: name);
      notifyListeners();
      return true;
    }
    return false;
  }

  /// Login với hỗ trợ Offline:
  /// 1. Thử online trước → nếu thành công, cache credentials
  /// 2. Nếu offline → so sánh hash cục bộ → cho phép vào app
  Future<String?> login(String username, String password) async {
    _isLoading = true;
    _isOfflineMode = false;
    notifyListeners();

    // Kiểm tra kết nối
    bool hasConnection = await _checkConnectivity();

    if (hasConnection) {
      // ===== ONLINE LOGIN =====
      try {
        final data = await _apiService.login(username, password);
        if (data['success'] == true) {
          final prefs = await SharedPreferences.getInstance();
          await prefs.setString('auth_token', data['token']);

          final u = data['user'];
          await prefs.setString('auth_username', u['username']);
          await prefs.setString('auth_name', u['name'] ?? '');
          await prefs.setString('auth_role', u['role'] ?? 'admin');

          // ★ Cache credentials cho offline login
          await _cacheCredentials(prefs, username, password);

          _user = UserModel.fromJson(u);
          _isLoading = false;
          _isOfflineMode = false;

          // Cập nhật FCM Token lên server sau khi đã có auth_token
          try {
            await FirebaseMessagingService().updateDeviceToken();
          } catch (e) {
            debugPrint("Không thể cập nhật FCM token lúc login: $e");
          }

          notifyListeners();
          return null; // Thành công
        } else {
          _isLoading = false;
          notifyListeners();
          return data['message'] ?? 'Đăng nhập thất bại';
        }
      } catch (e) {
        // API lỗi → thử offline fallback
        debugPrint('[AUTH] Online login failed, trying offline: $e');
        return _tryOfflineLogin(username, password);
      }
    } else {
      // ===== OFFLINE LOGIN =====
      return _tryOfflineLogin(username, password);
    }
  }

  /// Thử đăng nhập offline bằng cached credentials
  Future<String?> _tryOfflineLogin(String username, String password) async {
    final prefs = await SharedPreferences.getInstance();

    final cachedUsername = prefs.getString('cached_login_username');
    final cachedHash = prefs.getString('cached_login_hash');

    if (cachedUsername == null || cachedHash == null) {
      _isLoading = false;
      notifyListeners();
      return 'Không có kết nối mạng và chưa đăng nhập trước đó. Hãy kết nối Internet để đăng nhập lần đầu.';
    }

    // So sánh username + password hash
    final inputHash = _hashPassword(username, password);

    if (username == cachedUsername && inputHash == cachedHash) {
      // ★ Offline login thành công!
      final name = prefs.getString('auth_name') ?? username;
      final role = prefs.getString('auth_role') ?? 'admin';

      _user = UserModel(id: '0', username: username, role: role, name: name);
      _isOfflineMode = true;
      _isLoading = false;
      notifyListeners();
      return null; // Thành công (offline mode)
    } else {
      _isLoading = false;
      notifyListeners();
      return 'Thông tin đăng nhập offline không chính xác';
    }
  }

  /// Cache credentials: lưu username + hash(password) vào SharedPreferences
  Future<void> _cacheCredentials(
      SharedPreferences prefs, String username, String password) async {
    await prefs.setString('cached_login_username', username);
    await prefs.setString(
        'cached_login_hash', _hashPassword(username, password));
  }

  /// Hash password cục bộ (SHA-256 với salt = username)
  String _hashPassword(String username, String password) {
    final input = '$username:mtuface_salt:$password';
    return sha256.convert(utf8.encode(input)).toString();
  }

  /// Kiểm tra kết nối mạng
  Future<bool> _checkConnectivity() async {
    try {
      final result = await Connectivity().checkConnectivity();
      return !result.contains(ConnectivityResult.none);
    } catch (_) {
      return false;
    }
  }

  Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('auth_token');
    await prefs.remove('auth_username');
    await prefs.remove('auth_name');
    await prefs.remove('auth_role');
    // Không xóa cached_login_* để cho phép login offline lần sau
    _user = null;
    _isOfflineMode = false;
    notifyListeners();
  }
}
