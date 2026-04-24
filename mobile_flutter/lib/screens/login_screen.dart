
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import '../services/api_service.dart';
import 'register_screen.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  _LoginScreenState createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _usernameController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _isPasswordVisible = false;

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
          backgroundColor: const Color(0xFFE63946),
          behavior: SnackBarBehavior.floating,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = Provider.of<AuthProvider>(context);

    return Scaffold(
      body: Stack(
        children: [
          // Background Gradient
          Container(
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [
                  Color(0xFF1B3A5C), // MTU Deep Blue
                  Color(0xFF2E96EB), // MTU Action Blue
                ],
              ),
            ),
          ),
          
          // Decorative elements (Shapes)
          Positioned(
            top: -100,
            right: -100,
            child: CircleAvatar(radius: 150, backgroundColor: Colors.white.withOpacity(0.05)),
          ),
          Positioned(
            bottom: -50,
            left: -50,
            child: CircleAvatar(radius: 100, backgroundColor: Colors.black.withOpacity(0.05)),
          ),

          SafeArea(
            child: Center(
              child: SingleChildScrollView(
                padding: const EdgeInsets.symmetric(horizontal: 30),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    // Glass Card
                    Container(
                      padding: const EdgeInsets.all(32),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(28),
                        boxShadow: [
                          BoxShadow(
                            color: Colors.black.withOpacity(0.15),
                            blurRadius: 30,
                            offset: const Offset(0, 10),
                          ),
                        ],
                      ),
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          // Logo Section
                          Container(
                            padding: const EdgeInsets.all(12),
                            decoration: BoxDecoration(
                              color: Colors.white,
                              shape: BoxShape.circle,
                              boxShadow: [
                                BoxShadow(
                                  color: const Color(0xFF1B3A5C).withOpacity(0.1),
                                  blurRadius: 10,
                                )
                              ],
                            ),
                            child: ClipOval(
                              child: Image.asset(
                                "assets/images/logo_MTU.png",
                                width: 85,
                                height: 85,
                                fit: BoxFit.contain,
                                errorBuilder: (c, e, s) => Image.network(
                                  "logo_MTU.png",
                                  width: 85,
                                  height: 85,
                                  errorBuilder: (c, e, s) => const Icon(Icons.school, size: 50, color: Color(0xFF1B3A5C)),
                                ),
                              ),
                            ),
                          ),
                          const SizedBox(height: 20),
                          
                          const Text(
                            "MTU FACE ID",
                            style: TextStyle(
                              fontSize: 24, 
                              fontWeight: FontWeight.w900, 
                              color: Color(0xFF1B3A5C),
                              letterSpacing: 1.5,
                            ),
                          ),
                          const SizedBox(height: 8),
                          const Text(
                            "ĐẲNG CẤP QUỐC TẾ - CHẤT LƯỢNG HÀNG ĐẦU (BAO NGẦU) ",
                            textAlign: TextAlign.center,
                            style: TextStyle(
                              fontSize: 10, 
                              fontWeight: FontWeight.bold, 
                              color: Color(0xFF2E96EB),
                              letterSpacing: 0.5,
                            ),
                          ),
                          
                          const SizedBox(height: 35),

                          // Login Fields
                          _buildTextField(
                            controller: _usernameController,
                            label: "Tài khoản / MSSV",
                            icon: Icons.person_outline,
                          ),
                          const SizedBox(height: 20),
                          _buildTextField(
                            controller: _passwordController,
                            label: "Mật khẩu",
                            icon: Icons.lock_outline,
                            isPassword: true,
                          ),
                          
                          const SizedBox(height: 12),
                          Align(
                            alignment: Alignment.centerRight,
                            child: TextButton(
                              onPressed: () {},
                              child: const Text(
                                "Quên mật khẩu?",
                                style: TextStyle(color: Color(0xFF6C757D), fontSize: 13),
                              ),
                            ),
                          ),

                          const SizedBox(height: 12),
                          
                          // Sign In Button
                          SizedBox(
                            width: double.infinity,
                            height: 55,
                            child: ElevatedButton(
                              onPressed: auth.isLoading ? null : _handleLogin,
                              style: ElevatedButton.styleFrom(
                                backgroundColor: const Color(0xFF1B3A5C),
                                foregroundColor: Colors.white,
                                elevation: 4,
                                shadowColor: const Color(0xFF1B3A5C).withOpacity(0.5),
                                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                              ),
                              child: auth.isLoading
                                  ? const CircularProgressIndicator(color: Colors.white)
                                  : const Text(
                                      "ĐĂNG NHẬP",
                                      style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, letterSpacing: 1),
                                    ),
                            ),
                          ),

                          const SizedBox(height: 24),

                          // Register Support
                          Row(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              const Text(
                                "Chưa có tài khoản?",
                                style: TextStyle(color: Color(0xFF64748B), fontSize: 14),
                              ),
                              TextButton(
                                onPressed: () {
                                  Navigator.push(
                                    context,
                                    MaterialPageRoute(builder: (context) => const RegisterScreen()),
                                  );
                                },
                                child: const Text(
                                  "Đăng ký ngay",
                                  style: TextStyle(
                                    color: Color(0xFF2E96EB),
                                    fontWeight: FontWeight.bold,
                                    fontSize: 14,
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                    
                    const SizedBox(height: 40),
                    const Text(
                      "Đại học Xây dựng Miền Tây",
                      style: TextStyle(color: Colors.white70, fontWeight: FontWeight.w500, letterSpacing: 0.5),
                    ),
                    const Text(
                      "MTU Face Attendance System v2.0",
                      style: TextStyle(color: Colors.white54, fontSize: 12),
                    ),
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
    return TextField(
      controller: controller,
      obscureText: isPassword && !_isPasswordVisible,
      decoration: InputDecoration(
        labelText: label,
        labelStyle: TextStyle(color: Colors.grey[600], fontSize: 14),
        prefixIcon: Icon(icon, color: const Color(0xFF2E96EB), size: 22),
        suffixIcon: isPassword
            ? IconButton(
                icon: Icon(
                  _isPasswordVisible ? Icons.visibility : Icons.visibility_off,
                  color: Colors.grey,
                  size: 20,
                ),
                onPressed: () => setState(() => _isPasswordVisible = !_isPasswordVisible),
              )
            : null,
        filled: true,
        fillColor: Colors.grey[50]!.withOpacity(0.8),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: BorderSide(color: Colors.grey[200]!),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: const BorderSide(color: Color(0xFF2E96EB), width: 1.5),
        ),
      ),
    );
  }
}
