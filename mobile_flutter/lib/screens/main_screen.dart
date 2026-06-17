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
      extendBody: true, // Cho phép nội dung cuộn dưới BottomBar
      body: IndexedStack(
        index: _currentIndex,
        children: pages,
      ),
      
      // Floating Action Button (Nút nổi ở giữa)
      floatingActionButton: Container(
        height: 64,
        width: 64,
        margin: const EdgeInsets.only(top: 30),
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          gradient: const LinearGradient(
            colors: [AppTheme.secondary, AppTheme.primary],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
          boxShadow: [
            BoxShadow(
              color: AppTheme.primary.withOpacity(0.4),
              blurRadius: 16,
              offset: const Offset(0, 8),
            ),
          ],
        ),
        child: FloatingActionButton(
          onPressed: () {
            // Mở tính năng chính
            if (isAdmin) {
              Navigator.push(context, MaterialPageRoute(builder: (_) => const scan_screen.ScanScreen()));
            } else {
              Navigator.push(context, MaterialPageRoute(builder: (_) => const StudentQRScannerScreen()));
            }
          },
          backgroundColor: Colors.transparent,
          elevation: 0,
          highlightElevation: 0,
          child: Icon(
            isAdmin ? Icons.document_scanner : Icons.qr_code_scanner,
            color: Colors.white,
            size: 30,
          ),
        ),
      ),
      floatingActionButtonLocation: FloatingActionButtonLocation.centerDocked,

      // Bottom Navigation Bar
      bottomNavigationBar: Container(
        decoration: BoxDecoration(
          color: AppTheme.surface.withOpacity(0.9), // Glassmorphism background
          border: Border(top: BorderSide(color: Colors.white.withOpacity(0.05), width: 1)),
          boxShadow: [
            BoxShadow(color: Colors.black.withOpacity(0.3), blurRadius: 20, offset: const Offset(0, -5)),
          ],
        ),
        child: ClipRRect(
          child: BackdropFilter(
            filter: ImageFilter.blur(sigmaX: 20, sigmaY: 20),
            child: BottomAppBar(
              color: Colors.transparent,
              elevation: 0,
              notchMargin: 8,
              shape: const CircularNotchedRectangle(),
              child: SizedBox(
                height: 60,
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    _buildNavItem(icon: Icons.home_rounded, label: "Trang chủ", index: 0),
                    _buildNavItem(icon: Icons.calendar_month_rounded, label: isAdmin ? "Phiên" : "Điểm danh", index: 1),
                    const SizedBox(width: 48), // Khoảng trống cho FAB
                    _buildNavItem(icon: Icons.notifications_rounded, label: "Thông báo", index: 3),
                    _buildNavItem(icon: Icons.person_rounded, label: "Cá nhân", index: 4),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildNavItem({required IconData icon, required String label, required int index}) {
    final isSelected = _currentIndex == index;
    final color = isSelected ? AppTheme.secondary : AppTheme.textMuted;
    
    return Expanded(
      child: InkWell(
        onTap: () => setState(() => _currentIndex = index),
        highlightColor: Colors.transparent,
        splashColor: Colors.transparent,
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          mainAxisSize: MainAxisSize.min,
          children: [
            AnimatedContainer(
              duration: const Duration(milliseconds: 200),
              curve: Curves.easeOut,
              transform: Matrix4.identity()..scale(isSelected ? 1.1 : 1.0),
              child: Icon(icon, color: color, size: 24),
            ),
            const SizedBox(height: 4),
            AnimatedDefaultTextStyle(
              duration: const Duration(milliseconds: 200),
              style: TextStyle(
                color: color,
                fontSize: 10,
                fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
              ),
              child: Text(label),
            ),
          ],
        ),
      ),
    );
  }
}
