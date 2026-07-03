import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../theme/app_theme.dart';

class AboutScreen extends StatelessWidget {
  const AboutScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: AppBar(
        title: const Text("Về ứng dụng",
            style: TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: Colors.transparent,
        foregroundColor: AppTheme.textPrimary,
        elevation: 0,
      ),
      body: Stack(
        children: [
          // Ambient glow
          Positioned(
            top: -100,
            right: -100,
            child: ImageFiltered(
              imageFilter: ImageFilter.blur(sigmaX: 80, sigmaY: 80),
              child: Container(
                width: 300,
                height: 300,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: AppTheme.primary.withValues(alpha: 0.15),
                ),
              ),
            ),
          ),

          SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: Column(
              children: [
                // Logo
                Container(
                  padding: const EdgeInsets.all(20),
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: Colors.white.withValues(alpha: 0.08),
                    border: Border.all(
                        color: Colors.white.withValues(alpha: 0.15), width: 2),
                    boxShadow: [
                      BoxShadow(
                          color: AppTheme.primary.withValues(alpha: 0.3),
                          blurRadius: 30),
                    ],
                  ),
                  child: ClipOval(
                    child: Image.asset(
                      "assets/images/logo_MTU.png",
                      width: 80,
                      height: 80,
                      fit: BoxFit.contain,
                      errorBuilder: (c, e, s) => const Icon(Icons.school,
                          size: 60, color: AppTheme.secondary),
                    ),
                  ),
                )
                    .animate()
                    .fadeIn(duration: 400.ms)
                    .scale(begin: const Offset(0.8, 0.8)),

                const SizedBox(height: 20),

                const Text(
                  "MTU FACE ID",
                  style: TextStyle(
                    color: AppTheme.textPrimary,
                    fontSize: 28,
                    fontWeight: FontWeight.bold,
                    letterSpacing: 3,
                  ),
                ).animate().fadeIn(delay: 100.ms),

                const SizedBox(height: 8),

                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
                  decoration: BoxDecoration(
                    color: AppTheme.secondary.withValues(alpha: 0.15),
                    borderRadius: BorderRadius.circular(20),
                    border:
                        Border.all(color: AppTheme.secondary.withValues(alpha: 0.3)),
                  ),
                  child: const Text(
                    "Phiên bản 2.0",
                    style: TextStyle(
                        color: AppTheme.secondary,
                        fontSize: 13,
                        fontWeight: FontWeight.bold),
                  ),
                ).animate().fadeIn(delay: 200.ms),

                const SizedBox(height: 32),

                // Info cards
                _buildInfoSection(
                  icon: Icons.school,
                  title: "Trường",
                  value: "Đại Học Xây Dựng Miền Tây (MTU)",
                  delay: 300,
                ),
                _buildInfoSection(
                  icon: Icons.book,
                  title: "Đồ Án",
                  value: "Nhận Diện Khuôn Mặt - Điểm Danh Sinh Viên",
                  delay: 350,
                ),
                _buildInfoSection(
                  icon: Icons.person,
                  title: "Sinh viên thực hiện",
                  value: "Nguyễn Đông Từ",
                  delay: 400,
                ),
                _buildInfoSection(
                  icon: Icons.supervisor_account,
                  title: "Giảng viên hướng dẫn",
                  value: "Ths. Đặng Thị Xuân Tiên",
                  delay: 450,
                ),
                _buildInfoSection(
                  icon: Icons.calendar_today,
                  title: "Năm học",
                  value: "2025 - 2026",
                  delay: 500,
                ),

                const SizedBox(height: 24),

                // Tech stack
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(20),
                  decoration:
                      AppTheme.modernCardDecoration(borderRadius: 20, color: AppTheme.surfaceLight.withOpacity(0.05)),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        "CÔNG NGHỆ SỬ DỤNG",
                        style: TextStyle(
                          color: AppTheme.textSecondary,
                          fontSize: 12,
                          fontWeight: FontWeight.bold,
                          letterSpacing: 1,
                        ),
                      ),
                      const SizedBox(height: 16),
                      Wrap(
                        spacing: 8,
                        runSpacing: 8,
                        children: [
                          _techChip("Flutter", Icons.phone_android),
                          _techChip("Flask/Python", Icons.code),
                          _techChip("InsightFace AI", Icons.face),
                          _techChip("MySQL", Icons.storage),
                          _techChip("Firebase FCM", Icons.notifications),
                          _techChip("MiniFASNet", Icons.security),
                          _techChip("Google ML Kit", Icons.smart_toy),
                          _techChip("Ngrok Tunnel", Icons.cloud),
                        ],
                      ),
                    ],
                  ),
                ).animate().fadeIn(delay: 600.ms).slideY(begin: 0.1, end: 0),

                const SizedBox(height: 24),

                // Footer
                Text(
                  "© 2026 MTU Face Attendance System",
                  style: TextStyle(
                      color: AppTheme.textMuted.withValues(alpha: 0.5), fontSize: 12),
                ).animate().fadeIn(delay: 800.ms),

                const SizedBox(height: 40),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInfoSection({
    required IconData icon,
    required String title,
    required String value,
    required int delay,
  }) {
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: AppTheme.modernCardDecoration(
        color: AppTheme.surfaceLight.withOpacity(0.05),
        borderRadius: 20,
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: AppTheme.primary.withValues(alpha: 0.15),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(icon, color: AppTheme.secondary, size: 22),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title,
                    style: const TextStyle(
                        color: AppTheme.textMuted,
                        fontSize: 11,
                        fontWeight: FontWeight.w500)),
                const SizedBox(height: 4),
                Text(value,
                    style: const TextStyle(
                        color: AppTheme.textPrimary,
                        fontSize: 15,
                        fontWeight: FontWeight.w600)),
              ],
            ),
          ),
        ],
      ),
    )
        .animate()
        .fadeIn(delay: Duration(milliseconds: delay))
        .slideX(begin: 0.05, end: 0);
  }

  static Widget _techChip(String label, IconData icon) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: AppTheme.surfaceLight.withValues(alpha: 0.5),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.white.withValues(alpha: 0.08)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, color: AppTheme.secondary, size: 14),
          const SizedBox(width: 6),
          Text(label,
              style: const TextStyle(
                  color: AppTheme.textPrimary,
                  fontSize: 12,
                  fontWeight: FontWeight.w500)),
        ],
      ),
    );
  }
}
