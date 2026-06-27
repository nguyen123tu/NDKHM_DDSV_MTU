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
      extendBody: true, // Cho phép nội dung cuộn dưới BottomBar
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
      floatingActionButton: Padding(
        padding: const EdgeInsets.only(top: 20),
        child: NeuButton(
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
      ),
      floatingActionButtonLocation: FloatingActionButtonLocation.centerDocked,

      // --- Neumorphic / Glassmorphic Floating Tab Bar ---
      bottomNavigationBar: Container(
        margin: const EdgeInsets.only(left: 16, right: 16, bottom: 24), // Cách viền để lơ lửng
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(30),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.4),
              blurRadius: 20,
              offset: const Offset(5, 5),
            ),
            BoxShadow(
              color: Colors.white.withValues(alpha: 0.05), // Giảm độ chói của bóng sáng
              blurRadius: 20,
              offset: const Offset(-2, -2),
            ),
          ],
        ),
        child: ClipRRect(
          borderRadius: BorderRadius.circular(30),
          child: BackdropFilter(
            filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
            child: Container(
              height: 70,
              decoration: BoxDecoration(
                color: Theme.of(context).brightness == Brightness.dark 
                    ? AppTheme.surface.withValues(alpha: 0.8) 
                    : AppTheme.neuBackground.withValues(alpha: 0.85),
                borderRadius: BorderRadius.circular(30),
                border: Border.all(
                  color: Colors.white.withValues(alpha: 0.2),
                  width: 1.5,
                ),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                children: [
                  _buildNavItem(icon: Icons.home_rounded, label: "Trang chủ", index: 0),
                  _buildNavItem(icon: Icons.calendar_month_rounded, label: isAdmin ? "Phiên" : "Điểm danh", index: 1),
                  const SizedBox(width: 60), // Khoảng trống cho FAB
                  _buildNavItem(icon: Icons.notifications_rounded, label: "Thông báo", index: 3),
                  _buildNavItem(icon: Icons.person_rounded, label: "Cá nhân", index: 4),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildNavItem({required IconData icon, required String label, required int index}) {
    final isSelected = _currentIndex == index;
    final isDark = Theme.of(context).brightness == Brightness.dark;
    
    final activeColor = AppTheme.primary;
    final inactiveColor = isDark ? AppTheme.textMuted : AppTheme.textDarkSecondary.withValues(alpha: 0.6);
    
    return GestureDetector(
      onTap: () => setState(() => _currentIndex = index),
      behavior: HitTestBehavior.opaque,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 400),
        curve: Curves.fastOutSlowIn,
        padding: EdgeInsets.symmetric(horizontal: isSelected ? 18 : 10, vertical: 10),
        decoration: BoxDecoration(
          color: isSelected 
              ? activeColor.withValues(alpha: 0.15) 
              : Colors.transparent,
          borderRadius: BorderRadius.circular(24),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            AnimatedSwitcher(
              duration: const Duration(milliseconds: 300),
              transitionBuilder: (child, anim) => ScaleTransition(scale: anim, child: child),
              child: Icon(
                icon,
                key: ValueKey('$index-$isSelected'),
                color: isSelected ? activeColor : inactiveColor,
                size: isSelected ? 26 : 24,
              ),
            ),
            if (isSelected) ...[
              const SizedBox(width: 8),
              Text(
                label,
                style: TextStyle(
                  color: activeColor,
                  fontSize: 13,
                  fontWeight: FontWeight.bold,
                ),
              ).animate().fadeIn(duration: 300.ms).slideX(begin: 0.2, end: 0),
            ]
          ],
        ),
      ),
    );
  }
}
