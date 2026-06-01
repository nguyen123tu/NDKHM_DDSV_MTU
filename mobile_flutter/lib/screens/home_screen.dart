import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../providers/attendance_provider.dart';
import '../providers/auth_provider.dart';
import '../providers/connectivity_provider.dart';
import 'scan_screen.dart' as scan_screen;
import 'register_screen.dart' as reg_screen;
import 'profile_screen.dart';
import 'schedule_screen.dart';
import 'device_settings_screen.dart';
import 'history_report_screen.dart';
import 'face_approval_screen.dart';
import 'student_attendance_screen.dart';
import 'admin_session_screen.dart';
import 'student_qr_scanner_screen.dart';
import 'session_history_screen.dart';
import 'admin_stats_screen.dart';
import 'notifications_screen.dart';
import 'sync_status_screen.dart';
import 'chatbot_screen.dart';
import '../services/export_service.dart';
import '../services/api_service.dart';
import '../theme/app_theme.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  _HomeScreenState createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  bool _isHistoryCollapsed = false;
  bool _isFeaturesExpanded = false;
  final ApiService _api = ApiService();

  @override
  void initState() {
    super.initState();
    Future.microtask(() =>
        Provider.of<AttendanceProvider>(context, listen: false).fetchDashboardData());
  }

  String _getGreeting() {
    final hour = DateTime.now().hour;
    if (hour < 12) return "Good Morning";
    if (hour < 18) return "Good Afternoon";
    return "Good Evening";
  }

  @override
  Widget build(BuildContext context) {
    final auth = Provider.of<AuthProvider>(context);
    final attendance = Provider.of<AttendanceProvider>(context);
    final connectivity = Provider.of<ConnectivityProvider>(context);
    final isAdmin = auth.user?.role != 'student';
    final userName = auth.user?.name ?? 'Admin';

    return Scaffold(
      backgroundColor: AppTheme.background,
      body: Stack(
        children: [
          // Ambient Background Glows
          Positioned(
            top: -100,
            left: -100,
            child: Container(
              width: 300,
              height: 300,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: AppTheme.primary.withOpacity(0.2),
                backgroundBlendMode: BlendMode.screen,
              ),
            ).animate(onPlay: (controller) => controller.repeat(reverse: true))
             .scale(begin: const Offset(1, 1), end: const Offset(1.2, 1.2), duration: 4.seconds),
          ),
          Positioned(
            bottom: -50,
            right: -50,
            child: Container(
              width: 250,
              height: 250,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: AppTheme.secondary.withOpacity(0.15),
                backgroundBlendMode: BlendMode.screen,
              ),
            ).animate(onPlay: (controller) => controller.repeat(reverse: true))
             .scale(begin: const Offset(1, 1), end: const Offset(1.3, 1.3), duration: 5.seconds),
          ),

          // Main Content
          SafeArea(
            bottom: false,
            child: RefreshIndicator(
              color: AppTheme.secondary,
              backgroundColor: AppTheme.surface,
              onRefresh: () async {
                await attendance.fetchDashboardData();
                await connectivity.refreshPendingCount();
              },
              child: CustomScrollView(
                physics: const AlwaysScrollableScrollPhysics(),
                slivers: [
                  SliverToBoxAdapter(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        // ====== OFFLINE/SYNC BANNER ======
                        _buildSyncBanner(connectivity, auth),

                        // ====== APP BAR ======
                        Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
                          child: Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Row(
                                children: [
                                  Container(
                                    padding: const EdgeInsets.all(8),
                                    decoration: AppTheme.glassDecoration(opacity: 0.1, borderRadius: 12),
                                    child: const Icon(Icons.face_retouching_natural, color: AppTheme.secondary, size: 22),
                                  ),
                                  const SizedBox(width: 12),
                                  Text(
                                    "MTU FACE",
                                    style: Theme.of(context).textTheme.titleLarge?.copyWith(letterSpacing: 2),
                                  ),
                                ],
                              ).animate().fadeIn(duration: 400.ms).slideX(begin: -0.2, end: 0),
                              Row(
                                children: [
                                  if (isAdmin)
                                    Container(
                                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                                      margin: const EdgeInsets.only(right: 12),
                                      decoration: AppTheme.glassDecoration(opacity: 0.1, borderRadius: 20),
                                      child: const Row(
                                        children: [
                                          Icon(Icons.admin_panel_settings, color: AppTheme.secondary, size: 14),
                                          SizedBox(width: 4),
                                          Text("Admin", style: TextStyle(color: AppTheme.secondary, fontSize: 11, fontWeight: FontWeight.bold)),
                                        ],
                                      ),
                                    ).animate().fadeIn(delay: 100.ms),
                                  GestureDetector(
                                    onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const ProfileScreen())),
                                    child: Container(
                                      padding: const EdgeInsets.all(8),
                                      decoration: AppTheme.glassDecoration(shape: BoxShape.circle),
                                      child: const Icon(Icons.person, color: AppTheme.textPrimary, size: 20),
                                    ),
                                  ),
                                  const SizedBox(width: 12),
                                  GestureDetector(
                                    onTap: () => auth.logout(),
                                    child: Container(
                                      padding: const EdgeInsets.all(8),
                                      decoration: AppTheme.glassDecoration(shape: BoxShape.circle),
                                      child: const Icon(Icons.logout, color: AppTheme.accent, size: 20),
                                    ),
                                  ),
                                ],
                              ).animate().fadeIn(duration: 400.ms).slideX(begin: 0.2, end: 0),
                            ],
                          ),
                        ),

                        // ====== GREETING ======
                        Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                _getGreeting(),
                                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                  color: AppTheme.secondary,
                                  fontWeight: FontWeight.bold,
                                  letterSpacing: 1,
                                ),
                              ).animate().fadeIn(delay: 200.ms).slideY(begin: 0.2, end: 0),
                              const SizedBox(height: 4),
                              Row(
                                children: [
                                  Text(
                                    userName,
                                    style: Theme.of(context).textTheme.displayLarge?.copyWith(fontSize: 32),
                                  ).animate().fadeIn(delay: 300.ms).slideY(begin: 0.2, end: 0),
                                  if (auth.isOfflineMode)
                                    Padding(
                                      padding: const EdgeInsets.only(left: 12),
                                      child: Container(
                                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                        decoration: AppTheme.glassDecoration(color: AppTheme.warning, opacity: 0.2, borderRadius: 8),
                                        child: const Row(
                                          mainAxisSize: MainAxisSize.min,
                                          children: [
                                            Icon(Icons.cloud_off, color: AppTheme.warning, size: 12),
                                            SizedBox(width: 4),
                                            Text('Offline', style: TextStyle(color: AppTheme.warning, fontSize: 10, fontWeight: FontWeight.bold)),
                                          ],
                                        ),
                                      ),
                                    ).animate().fadeIn(delay: 400.ms),
                                ],
                              ),
                            ],
                          ),
                        ),

                        // ====== STATS CARDS ======
                        Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 24),
                          child: _buildStatsGrid(attendance).animate().fadeIn(delay: 400.ms).scale(begin: const Offset(0.95, 0.95), end: const Offset(1, 1)),
                        ),

                        const SizedBox(height: 32),

                        // ====== MAIN ACTIONS ======
                        Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 24),
                          child: _buildMainActions(isAdmin, auth.isOfflineMode).animate().fadeIn(delay: 500.ms).slideY(begin: 0.1, end: 0),
                        ),

                        const SizedBox(height: 32),

                        // ====== RECENT HISTORY ======
                        _buildRecentHistorySection(attendance, isAdmin).animate().fadeIn(delay: 600.ms).slideY(begin: 0.1, end: 0),

                        const SizedBox(height: 100), // padding bottom
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  // ====== Offline/Sync Banner ======
  Widget _buildSyncBanner(ConnectivityProvider connectivity, AuthProvider auth) {
    if (connectivity.isOnline && connectivity.pendingSyncCount == 0 && !connectivity.isSyncing && !auth.isOfflineMode) {
      return const SizedBox.shrink();
    }

    Color glowColor;
    IconData icon;
    String message;

    if (!connectivity.isOnline) {
      glowColor = AppTheme.error;
      icon = Icons.cloud_off;
      message = 'Offline';
      if (connectivity.pendingSyncCount > 0) message += ' • ${connectivity.pendingSyncCount} pending';
    } else if (connectivity.isSyncing) {
      glowColor = AppTheme.secondary;
      icon = Icons.sync;
      message = connectivity.syncMessage ?? 'Syncing...';
    } else if (connectivity.pendingSyncCount > 0) {
      glowColor = AppTheme.warning;
      icon = Icons.pending_outlined;
      message = '${connectivity.pendingSyncCount} pending syncs';
    } else {
      glowColor = AppTheme.success;
      icon = Icons.cloud_done;
      message = connectivity.syncMessage ?? 'Synced';
    }

    return GestureDetector(
      onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const SyncStatusScreen())),
      child: Container(
        margin: const EdgeInsets.fromLTRB(24, 0, 24, 16),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        decoration: AppTheme.glassDecoration(
          color: glowColor,
          opacity: 0.15,
          borderRadius: 16,
        ).copyWith(
          border: Border.all(color: glowColor.withOpacity(0.5), width: 1),
          boxShadow: [
            BoxShadow(color: glowColor.withOpacity(0.2), blurRadius: 12, spreadRadius: 0),
          ],
        ),
        child: Row(
          children: [
            if (connectivity.isSyncing)
              SizedBox(
                width: 16, height: 16,
                child: CircularProgressIndicator(color: glowColor, strokeWidth: 2),
              )
            else
              Icon(icon, color: glowColor, size: 16),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                message,
                style: TextStyle(color: glowColor, fontSize: 13, fontWeight: FontWeight.w600),
              ),
            ),
            if (connectivity.isOnline && connectivity.pendingSyncCount > 0 && !connectivity.isSyncing)
              GestureDetector(
                onTap: () => connectivity.manualSync(),
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  decoration: BoxDecoration(
                    color: glowColor.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text('SYNC NOW', style: TextStyle(color: glowColor, fontSize: 10, fontWeight: FontWeight.bold, letterSpacing: 1)),
                ),
              ),
            if (!connectivity.isOnline)
              Icon(Icons.chevron_right, color: glowColor.withOpacity(0.8), size: 18),
          ],
        ),
      ),
    ).animate().fadeIn().slideY(begin: -0.5, end: 0);
  }

  // ====== Stats Grid ======
  Widget _buildStatsGrid(AttendanceProvider attendance) {
    if (attendance.isLoading && attendance.stats == null) {
      return const Center(child: CircularProgressIndicator(color: AppTheme.secondary));
    }

    final stats = attendance.stats;
    return Row(
      children: [
        Expanded(
          child: _buildGlassStatCard(
            title: "Tổng SV",
            value: "${stats?.total ?? 0}",
            icon: Icons.people_alt,
            color: AppTheme.primary,
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: _buildGlassStatCard(
            title: "Có mặt",
            value: "${stats?.present ?? 0}",
            icon: Icons.how_to_reg,
            color: AppTheme.success,
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: _buildGlassStatCard(
            title: "Vắng",
            value: "${stats?.absent ?? 0}",
            icon: Icons.person_off,
            color: AppTheme.error,
          ),
        ),
      ],
    );
  }

  Widget _buildGlassStatCard({required String title, required String value, required IconData icon, required Color color}) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 12),
      decoration: AppTheme.glassDecoration(borderRadius: 20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: color, size: 24),
          const SizedBox(height: 12),
          Text(value, style: const TextStyle(color: AppTheme.textPrimary, fontSize: 24, fontWeight: FontWeight.bold)),
          const SizedBox(height: 4),
          Text(title, style: const TextStyle(color: AppTheme.textSecondary, fontSize: 12)),
        ],
      ),
    );
  }

  // ====== Main Actions ======
  Widget _buildMainActions(bool isAdmin, bool isOffline) {
    return Column(
      children: [
        Row(
          children: [
            Expanded(
              flex: 3,
              child: _buildActionCard(
                title: "Scan Face",
                subtitle: isOffline ? "Offline Mode" : "AI Recognition",
                icon: Icons.center_focus_strong,
                gradient: const [AppTheme.secondary, AppTheme.primary],
                onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const scan_screen.ScanScreen())),
              ),
            ),
            const SizedBox(width: 12),
            if (isAdmin)
              Expanded(
                flex: 2,
                child: _buildActionCard(
                  title: "Register",
                  subtitle: "New Face",
                  icon: Icons.person_add,
                  gradient: const [Color(0xFF8B5CF6), Color(0xFF6D28D9)],
                  onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const reg_screen.RegisterScreen())),
                ),
              )
            else
              Expanded(
                flex: 2,
                child: _buildActionCard(
                  title: "Lịch Học",
                  subtitle: "Schedule",
                  icon: Icons.calendar_today,
                  gradient: const [Color(0xFF8B5CF6), Color(0xFF6D28D9)],
                  onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const ScheduleScreen())),
                ),
              ),
          ],
        ),
        Padding(
          padding: const EdgeInsets.only(top: 12),
          child: Row(
            children: [
              Expanded(
                child: _buildSecondaryAction(
                  title: "QR Scan",
                  icon: Icons.qr_code_scanner,
                  onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const StudentQRScannerScreen())),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _buildSecondaryAction(
                  title: "AI Chat",
                  icon: Icons.auto_awesome,
                  onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const ChatbotScreen())),
                ),
              ),
              const SizedBox(width: 12),
              if (isAdmin) ...[
                Expanded(
                  child: _buildSecondaryAction(
                    title: "Sessions",
                    icon: Icons.event,
                    onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const AdminSessionScreen())),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _buildSecondaryAction(
                    title: "Stats",
                    icon: Icons.bar_chart,
                    onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const AdminStatsScreen())),
                  ),
                ),
              ] else ...[
                Expanded(
                  child: _buildSecondaryAction(
                    title: "Thông báo",
                    icon: Icons.notifications,
                    onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const NotificationsScreen())),
                  ),
                ),
              ],
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildActionCard({required String title, required String subtitle, required IconData icon, required List<Color> gradient, required VoidCallback onTap}) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          gradient: LinearGradient(colors: gradient, begin: Alignment.topLeft, end: Alignment.bottomRight),
          borderRadius: BorderRadius.circular(24),
          boxShadow: [
            BoxShadow(color: gradient.first.withOpacity(0.3), blurRadius: 16, offset: const Offset(0, 8)),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(color: Colors.white.withOpacity(0.2), shape: BoxShape.circle),
              child: Icon(icon, color: Colors.white, size: 28),
            ),
            const SizedBox(height: 16),
            Text(title, style: const TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold)),
            const SizedBox(height: 4),
            Text(subtitle, style: TextStyle(color: Colors.white.withOpacity(0.8), fontSize: 12)),
          ],
        ),
      ),
    );
  }

  Widget _buildSecondaryAction({required String title, required IconData icon, required VoidCallback onTap}) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 16),
        decoration: AppTheme.glassDecoration(borderRadius: 16),
        child: Column(
          children: [
            Icon(icon, color: AppTheme.secondary, size: 24),
            const SizedBox(height: 8),
            Text(title, style: const TextStyle(color: AppTheme.textPrimary, fontSize: 12, fontWeight: FontWeight.w600)),
          ],
        ),
      ),
    );
  }

  // ====== Recent History ======
  Widget _buildRecentHistorySection(AttendanceProvider attendance, bool isAdmin) {
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text("Lịch sử gần đây", style: TextStyle(color: AppTheme.textPrimary, fontSize: 18, fontWeight: FontWeight.bold)),
              TextButton(
                onPressed: () {
                  setState(() => _isHistoryCollapsed = !_isHistoryCollapsed);
                },
                child: Text(_isHistoryCollapsed ? "Hiện" : "Ẩn", style: const TextStyle(color: AppTheme.secondary)),
              ),
            ],
          ),
        ),
        if (!_isHistoryCollapsed)
          attendance.isLoading && attendance.history.isEmpty
              ? const Padding(padding: EdgeInsets.all(32), child: Center(child: CircularProgressIndicator(color: AppTheme.secondary)))
              : attendance.history.isEmpty
                  ? Padding(
                      padding: const EdgeInsets.all(32),
                      child: Center(
                        child: Text("Chưa có dữ liệu hôm nay.", style: TextStyle(color: AppTheme.textMuted, fontStyle: FontStyle.italic)),
                      ),
                    )
                  : ListView.builder(
                      shrinkWrap: true,
                      physics: const NeverScrollableScrollPhysics(),
                      itemCount: attendance.history.length > 5 ? 5 : attendance.history.length,
                      padding: const EdgeInsets.symmetric(horizontal: 16),
                      itemBuilder: (context, index) {
                        final record = attendance.history[index];
                        return _buildHistoryGlassCard(record, isAdmin, index);
                      },
                    ),
      ],
    );
  }

  String _getAvatarUrl(String? avatarPath) {
    if (avatarPath == null || avatarPath.isEmpty) return "";
    if (avatarPath.startsWith("uploads/")) {
      return "${ApiService.baseUrl}/static/$avatarPath";
    }
    return "${ApiService.baseUrl}/database/$avatarPath";
  }

  Widget _buildHistoryGlassCard(dynamic record, bool isAdmin, int index) {
    final isOffline = record.trangThai == 'Unknown' || record.mssv == 'OFFLINE_PENDING';
    
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      decoration: AppTheme.glassDecoration(borderRadius: 16, opacity: 0.05, border: false),
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        leading: Container(
          width: 48, height: 48,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            border: Border.all(color: isOffline ? AppTheme.warning : AppTheme.secondary, width: 2),
            image: record.avatar != null && record.avatar!.isNotEmpty
                ? DecorationImage(image: NetworkImage(_getAvatarUrl(record.avatar)), fit: BoxFit.cover)
                : null,
          ),
          child: record.avatar == null || record.avatar!.isEmpty
              ? Icon(Icons.person, color: isOffline ? AppTheme.warning : AppTheme.secondary)
              : null,
        ),
        title: Text(
          isOffline ? "Bản ghi Offline" : (record.hoTen ?? 'Unknown'),
          style: const TextStyle(color: AppTheme.textPrimary, fontWeight: FontWeight.bold),
        ),
        subtitle: Text(
          isOffline ? "Đang chờ đồng bộ" : "${record.mssv} • Lớp ${record.maLop}",
          style: const TextStyle(color: AppTheme.textSecondary, fontSize: 12),
        ),
        trailing: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Text(
              _formatTimeFromISO(record.thoiGian),
              style: const TextStyle(color: AppTheme.textPrimary, fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 4),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
              decoration: BoxDecoration(
                color: isOffline ? AppTheme.warning.withOpacity(0.2) : AppTheme.success.withOpacity(0.2),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(
                isOffline ? "Pending" : "✓ Điểm danh",
                style: TextStyle(color: isOffline ? AppTheme.warning : AppTheme.success, fontSize: 10, fontWeight: FontWeight.bold),
              ),
            ),
          ],
        ),
      ),
    ).animate().fadeIn(delay: Duration(milliseconds: 600 + (index * 100))).slideX(begin: 0.1, end: 0);
  }

  String _formatTimeFromISO(String? isoString) {
    if (isoString == null || isoString.isEmpty) return "--:--";
    try {
      final dt = DateTime.parse(isoString).toLocal();
      return '${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}';
    } catch (e) {
      if (isoString.length > 16) {
        return isoString.substring(11, 16);
      }
      return isoString;
    }
  }
}
