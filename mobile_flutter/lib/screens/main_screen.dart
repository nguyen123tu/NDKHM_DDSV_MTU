import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import '../theme/app_theme.dart';
import 'home_screen.dart';
import 'scan_screen.dart' as scan_screen;
import 'student_qr_scanner_screen.dart';
import 'admin_session_screen.dart';
import 'student_attendance_screen.dart';
import 'notifications_screen.dart';
import 'profile_screen.dart';
import '../widgets/neu_button.dart';
import 'package:flutter_animate/flutter_animate.dart';

class MainScreen extends StatefulWidget {
  const MainScreen({super.key});

  @override
  State<MainScreen> createState() => _MainScreenState();
}

class _MainScreenState extends State<MainScreen> {
  int _currentIndex = 0;

  @override
  Widget build(BuildContext context) {
    final auth = Provider.of<AuthProvider>(context);
    final isAdmin = auth.user?.role != 'student';

    // Xác định các màn hình tương ứng với từng tab
    final List<Widget> pages = [
      const HomeScreen(), // 0: Trang chủ
      isAdmin ? const AdminSessionScreen() : const StudentAttendanceScreen(), // 1: Lịch sử/Phiên
      const SizedBox(), // 2: Placeholder cho FAB ở giữa
      const NotificationsScreen(), // 3: Thông báo
      const ProfileScreen(), // 4: Cá nhân
    ];

    return Scaffold(
      backgroundColor: AppTheme.background,
      extendBody: false, // Tắt extendBody để thanh BottomBar không che mất nội dung
      body: Stack(
        children: List.generate(pages.length, (index) {
          if (index == 2) return const SizedBox(); // Placeholder for FAB
          final isSelected = _currentIndex == index;
          return IgnorePointer(
            ignoring: !isSelected,
            child: AnimatedOpacity(
              duration: const Duration(milliseconds: 350),
              curve: Curves.easeInOut,
              opacity: isSelected ? 1.0 : 0.0,
              child: AnimatedSlide(
                duration: const Duration(milliseconds: 350),
                curve: Curves.easeOutCubic,
                offset: isSelected ? Offset.zero : const Offset(0.0, 0.05),
                child: pages[index],
              ),
            ),
          );
        }),
      ),
      
      // Floating Action Button (Nút nổi ở giữa - thiết kế lại theo Neu/Glass)
      floatingActionButton: NeuButton(
        shape: BoxShape.circle,
        isPrimary: true,
        padding: const EdgeInsets.all(16),
        onPressed: () {
          if (isAdmin) {
            Navigator.push(context, MaterialPageRoute(builder: (_) => const scan_screen.ScanScreen()));
          } else {
            Navigator.push(context, MaterialPageRoute(builder: (_) => const StudentQRScannerScreen()));
          }
        },
        child: Icon(
          isAdmin ? Icons.document_scanner : Icons.qr_code_scanner,
          color: Colors.white,
          size: 30,
        ),
      ),
      floatingActionButtonLocation: FloatingActionButtonLocation.centerDocked,

      // --- Modern Standard Bottom App Bar ---
      bottomNavigationBar: BottomAppBar(
        color: AppTheme.surface,
        elevation: 20,
        shape: const CircularNotchedRectangle(),
        notchMargin: 8,
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Row(
              children: [
                _buildNavItem(icon: Icons.home_rounded, label: "Trang chủ", index: 0),
                const SizedBox(width: 8),
                _buildNavItem(icon: Icons.calendar_month_rounded, label: isAdmin ? "Phiên" : "Điểm danh", index: 1),
              ],
            ),
            Row(
              children: [
                _buildNavItem(icon: Icons.notifications_rounded, label: "Thông báo", index: 3),
                const SizedBox(width: 8),
                _buildNavItem(icon: Icons.person_rounded, label: "Cá nhân", index: 4),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildNavItem({required IconData icon, required String label, required int index}) {
    final isSelected = _currentIndex == index;
    final isDark = Theme.of(context).brightness == Brightness.dark;
    
    final activeColor = isDark ? AppTheme.secondary : AppTheme.primary;
    final inactiveColor = isDark ? AppTheme.textMuted : AppTheme.textSecondary.withValues(alpha: 0.6);
    
    return InkWell(
      onTap: () => setState(() => _currentIndex = index),
      borderRadius: BorderRadius.circular(16),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            AnimatedContainer(
              duration: const Duration(milliseconds: 300),
              padding: EdgeInsets.symmetric(horizontal: isSelected ? 16 : 0, vertical: 4),
              decoration: BoxDecoration(
                color: isSelected ? activeColor.withOpacity(0.15) : Colors.transparent,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Icon(
                icon,
                color: isSelected ? activeColor : inactiveColor,
                size: 24,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              label,
              style: TextStyle(
                color: isSelected ? activeColor : inactiveColor,
                fontSize: 11,
                fontWeight: isSelected ? FontWeight.bold : FontWeight.w500,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
