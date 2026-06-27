import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:local_auth/local_auth.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../providers/auth_provider.dart';
import 'register_screen.dart';
import '../theme/app_theme.dart';
import '../widgets/neu_container.dart';
import '../widgets/neu_button.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  _LoginScreenState createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _usernameController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _isPasswordVisible = false;

  final LocalAuthentication _localAuth = LocalAuthentication();
  bool _canCheckBiometrics = false;
  bool _hasSavedToken = false;

  @override
  void initState() {
    super.initState();
    _checkBiometrics();
  }

  Future<void> _checkBiometrics() async {
    try {
      final isSupported = await _localAuth.isDeviceSupported();
      final canCheck = await _localAuth.canCheckBiometrics;

      final prefs = await SharedPreferences.getInstance();
      final token = prefs.getString('auth_token');

      setState(() {
        _canCheckBiometrics = isSupported || canCheck;
        _hasSavedToken = token != null;
      });

      // Auto-trigger biometric if they have a saved token
      if (_hasSavedToken && _canCheckBiometrics) {
        _authenticateWithBiometrics();
      }
    } catch (e) {
      debugPrint("Biometric check error: $e");
      // Fallback
      setState(() {
        _canCheckBiometrics = true;
      });
    }
  }

  Future<void> _authenticateWithBiometrics() async {
    try {
      final authenticated = await _localAuth.authenticate(
        localizedReason: 'Xác thực vân tay/Face ID để đăng nhập',
      );

      if (authenticated && mounted) {
        final auth = Provider.of<AuthProvider>(context, listen: false);
        final success = await auth.loginWithCachedToken();
        if (!success) {
          if (mounted) {
            ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
                content: Text(
                    'Vui lòng đăng nhập bằng mật khẩu để kích hoạt sinh trắc học!'),
                backgroundColor: AppTheme.error));
          }
        }
      }
    } catch (e) {
      debugPrint("Biometric auth error: $e");
    }
  }

  void _handleLogin() async {
    final auth = Provider.of<AuthProvider>(context, listen: false);
    final error = await auth.login(
      _usernameController.text.trim(),
      _passwordController.text.trim(),
    );

    if (error != null && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(error),
          backgroundColor: AppTheme.error,
          behavior: SnackBarBehavior.floating,
          shape:
              RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = Provider.of<AuthProvider>(context);

    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      body: Stack(
        children: [
          // Background - Clean Neumorphism
          Container(color: Theme.of(context).scaffoldBackgroundColor),

          SafeArea(
            child: Center(
              child: SingleChildScrollView(
                padding: const EdgeInsets.symmetric(horizontal: 24),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    // Neumorphic Card
                    NeuContainer(
                      padding: const EdgeInsets.all(32),
                      borderRadius: 32,
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          // Logo Section
                          NeuContainer(
                            padding: const EdgeInsets.all(16),
                            shape: BoxShape.circle,
                            child: ClipOval(
                              child: Image.asset(
                                "assets/images/logo_MTU.png",
                                width: 80,
                                height: 80,
                                fit: BoxFit.contain,
                                errorBuilder: (c, e, s) => Image.network(
                                  "logo_MTU.png",
                                  width: 80,
                                  height: 80,
                                  errorBuilder: (c, e, s) => const Icon(
                                      Icons.school,
                                      size: 50,
                                      color: AppTheme.textPrimary),
                                ),
                              ),
                            ),
                          ).animate().fadeIn(duration: 300.ms).scale(
                              begin: const Offset(0.9, 0.9),
                              end: const Offset(1, 1)),
                          const SizedBox(height: 24),

                          Text(
                            "MTU FACE ID",
                            style: Theme.of(context)
                                .textTheme
                                .displayLarge
                                ?.copyWith(
                                  fontSize: 28,
                                  letterSpacing: 2,
                                ),
                          ).animate().fadeIn(delay: 100.ms),
                          const SizedBox(height: 8),
                          const Text(
                            "HỆ THỐNG ĐIỂM DANH THÔNG MINH",
                            textAlign: TextAlign.center,
                            style: TextStyle(
                              fontSize: 10,
                              fontWeight: FontWeight.bold,
                              color: AppTheme.secondary,
                              letterSpacing: 1,
                            ),
                          ).animate().fadeIn(delay: 150.ms),

                          const SizedBox(height: 40),

                          // Login Fields
                          _buildTextField(
                            controller: _usernameController,
                            label: "Tài khoản / MSSV",
                            icon: Icons.person_outline,
                          ).animate().fadeIn(delay: 200.ms),
                          const SizedBox(height: 20),
                          _buildTextField(
                            controller: _passwordController,
                            label: "Mật khẩu",
                            icon: Icons.lock_outline,
                            isPassword: true,
                          ).animate().fadeIn(delay: 250.ms),

                          const SizedBox(height: 12),
                          Align(
                            alignment: Alignment.centerRight,
                            child: TextButton(
                              onPressed: () {
                                showDialog(
                                  context: context,
                                  builder: (context) => AlertDialog(
                                    backgroundColor: AppTheme.surface,
                                    title: const Text("Quên mật khẩu",
                                        style: TextStyle(
                                            color: AppTheme.textPrimary)),
                                    content: const Text(
                                      "Vui lòng liên hệ với Quản trị viên (Admin) hoặc Giáo viên chủ nhiệm để được cấp lại mật khẩu mới.\n\nAdmin có thể dễ dàng cấp lại mật khẩu cho bạn thông qua trang Quản lý Web.",
                                      style: TextStyle(
                                          color: AppTheme.textSecondary,
                                          height: 1.5),
                                    ),
                                    actions: [
                                      TextButton(
                                        onPressed: () => Navigator.pop(context),
                                        child: const Text("Đã hiểu",
                                            style: TextStyle(
                                                color: AppTheme.primary,
                                                fontWeight: FontWeight.bold)),
                                      ),
                                    ],
                                  ),
                                );
                              },
                              child: const Text(
                                "Quên mật khẩu?",
                                style: TextStyle(
                                    color: AppTheme.textSecondary,
                                    fontSize: 13),
                              ),
                            ),
                          ).animate().fadeIn(delay: 300.ms),

                          const SizedBox(height: 12),

                          // Sign In Button
                          SizedBox(
                            width: double.infinity,
                            child: NeuButton(
                              isPrimary: true,
                              onPressed: auth.isLoading ? null : _handleLogin,
                              child: Center(
                                child: auth.isLoading
                                    ? const SizedBox(
                                        height: 20,
                                        width: 20,
                                        child: CircularProgressIndicator(
                                            color: Colors.white, strokeWidth: 2),
                                      )
                                    : const Text("ĐĂNG NHẬP", style: TextStyle(fontWeight: FontWeight.bold)),
                              ),
                            ),
                          ).animate().fadeIn(delay: 350.ms),

                          const SizedBox(height: 16),

                          // Biometric Login Button
                          if (_canCheckBiometrics) ...[
                            SizedBox(
                              width: double.infinity,
                              child: NeuButton(
                                onPressed: auth.isLoading
                                    ? null
                                    : () {
                                        if (!_hasSavedToken) {
                                          ScaffoldMessenger.of(context)
                                              .showSnackBar(const SnackBar(
                                                  content: Text(
                                                      'Bạn chưa có tài khoản đăng nhập cũ. Vui lòng đăng nhập bằng mật khẩu trước!'),
                                                  backgroundColor:
                                                      AppTheme.error));
                                        } else {
                                          _authenticateWithBiometrics();
                                        }
                                      },
                                child: const Row(
                                  mainAxisAlignment: MainAxisAlignment.center,
                                  children: [
                                    Icon(Icons.fingerprint, size: 28),
                                    SizedBox(width: 12),
                                    Text("Vân tay / Face ID", style: TextStyle(fontWeight: FontWeight.bold)),
                                  ],
                                ),
                              ),
                            ).animate().fadeIn(delay: 380.ms),
                            const SizedBox(height: 16),
                          ],

                          // Register Support
                          Wrap(
                            alignment: WrapAlignment.center,
                            crossAxisAlignment: WrapCrossAlignment.center,
                            children: [
                              const Text(
                                "Chưa có tài khoản?",
                                style: TextStyle(
                                    color: AppTheme.textMuted, fontSize: 14),
                              ),
                              TextButton(
                                onPressed: () {
                                  Navigator.push(
                                    context,
                                    MaterialPageRoute(
                                        builder: (context) =>
                                            const RegisterScreen()),
                                  );
                                },
                                child: const Text(
                                  "Đăng ký ngay",
                                  style: TextStyle(
                                    color: AppTheme.secondary,
                                    fontWeight: FontWeight.bold,
                                    fontSize: 14,
                                  ),
                                ),
                              ),
                            ],
                          ).animate().fadeIn(delay: 400.ms),
                        ],
                      ),
                    ),

                    const SizedBox(height: 40),
                    const Text(
                      "Đại học Xây dựng Miền Tây",
                      style: TextStyle(
                          color: AppTheme.textSecondary,
                          fontWeight: FontWeight.w500,
                          letterSpacing: 0.5),
                    ).animate().fadeIn(delay: 400.ms),
                    const SizedBox(height: 4),
                    const Text(
                      "MTU Face Attendance System v2.0",
                      style: TextStyle(color: AppTheme.textMuted, fontSize: 12),
                    ).animate().fadeIn(delay: 400.ms),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTextField({
    required TextEditingController controller,
    required String label,
    required IconData icon,
    bool isPassword = false,
  }) {
    return NeuContainer(
      isPressed: true, // Lõm xuống (Sunken effect) cho input
      borderRadius: 16,
      child: TextField(
        controller: controller,
        obscureText: isPassword && !_isPasswordVisible,
        style: const TextStyle(color: AppTheme.textPrimary),
        decoration: InputDecoration(
          labelText: label,
          labelStyle:
              const TextStyle(color: AppTheme.textSecondary, fontSize: 14),
          prefixIcon: Icon(icon, color: AppTheme.secondary, size: 22),
          suffixIcon: isPassword
              ? IconButton(
                  icon: Icon(
                    _isPasswordVisible
                        ? Icons.visibility
                        : Icons.visibility_off,
                    color: AppTheme.textSecondary,
                    size: 20,
                  ),
                  onPressed: () =>
                      setState(() => _isPasswordVisible = !_isPasswordVisible),
                )
              : null,
          filled: false,
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(16),
            borderSide: BorderSide.none,
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(16),
            borderSide: BorderSide(
                color: AppTheme.primary.withValues(alpha: 0.5), width: 1.5),
          ),
        ),
      ),
    );
  }
}
