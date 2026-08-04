import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../providers/attendance_provider.dart';
import '../providers/auth_provider.dart';
import '../providers/connectivity_provider.dart';
import 'register_screen.dart' as reg_screen;
import 'profile_screen.dart';
import 'schedule_screen.dart';
import 'device_settings_screen.dart';
import 'admin_session_screen.dart';
import 'admin_student_list_screen.dart' as admin_student;
import 'student_qr_scanner_screen.dart';
import 'admin_stats_screen.dart';
import 'notifications_screen.dart';
import 'sync_status_screen.dart';
import 'chatbot_screen.dart';
import 'about_screen.dart';
import '../services/api_service.dart';
import '../theme/app_theme.dart';
import '../widgets/neu_container.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  _HomeScreenState createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final bool _isFeaturesExpanded = false;
  final ApiService _api = ApiService();
  int _unreadNotifCount = 0;

  @override
  void initState() {
    super.initState();
    Future.microtask(() {
      Provider.of<AttendanceProvider>(context, listen: false)
          .fetchDashboardData();
      _fetchUnreadCount();
    });
  }

  Future<void> _fetchUnreadCount() async {
    try {
      final res = await _api.getNotifications();
      if (res['success'] == true && mounted) {
        final list = res['data'] as List? ?? [];
        final unread =
            list.where((n) => n['da_doc'] == 0 || n['da_doc'] == false).length;
        setState(() => _unreadNotifCount = unread);
      }
    } catch (_) {}
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
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      body: Stack(
        children: [
          // Background - Modern Deep Slate
          Container(color: AppTheme.background),

          // Glowing Orbs (Mesh Gradient Effect)
          Positioned(
            top: -100,
            right: -100,
            child: Container(
              width: 300,
              height: 300,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: AppTheme.primary.withOpacity(0.12),
              ),
            ),
          ).animate().fadeIn(duration: 1000.ms),

          Positioned(
            bottom: 100,
            left: -150,
            child: Container(
              width: 250,
              height: 250,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: AppTheme.accent.withOpacity(0.08),
              ),
            ),
          ).animate().fadeIn(duration: 1000.ms, delay: 300.ms),

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
                          padding: const EdgeInsets.symmetric(
                              horizontal: 24, vertical: 16),
                          child: Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Row(
                                children: [
                                  Container(
                                    padding: const EdgeInsets.all(12),
                                    decoration: BoxDecoration(
                                      shape: BoxShape.circle,
                                      gradient: AppTheme.primaryGradient,
                                    ),
                                    child: const Icon(
                                        Icons.face_retouching_natural,
                                        color: Colors.white,
                                        size: 24),
                                  ),
                                  const SizedBox(width: 12),
                                  Text(
                                    "MTU FACE",
                                    style: Theme.of(context)
                                        .textTheme
                                        .titleLarge
                                        ?.copyWith(letterSpacing: 2),
                                  ),
                                ],
                              ).animate().fadeIn(duration: 200.ms),
                              Row(
                                children: [
                                  if (isAdmin)
                                    NeuContainer(
                                      padding: const EdgeInsets.symmetric(
                                          horizontal: 12, vertical: 8),
                                      margin: const EdgeInsets.only(right: 12),
                                      borderRadius: 20,
                                      child: const Row(
                                        children: [
                                          Icon(Icons.admin_panel_settings,
                                              color: AppTheme.secondary,
                                              size: 14),
                                          SizedBox(width: 4),
                                          Text("Admin",
                                              style: TextStyle(
                                                  color: AppTheme.secondary,
                                                  fontSize: 11,
                                                  fontWeight: FontWeight.bold)),
                                        ],
                                      ),
                                    ).animate().fadeIn(delay: 100.ms),
                                  // Notification Bell with Badge
                                  GestureDetector(
                                    onTap: () {
                                      Navigator.push(
                                              context,
                                              MaterialPageRoute(
                                                  builder: (_) =>
                                                      const NotificationsScreen()))
                                          .then((_) => _fetchUnreadCount());
                                    },
                                    child: NeuContainer(
                                      padding: const EdgeInsets.all(10),
                                      shape: BoxShape.circle,
                                      child: Stack(
                                        clipBehavior: Clip.none,
                                        children: [
                                          const Icon(Icons.notifications_none,
                                              color: AppTheme.textPrimary,
                                              size: 20),
                                          if (_unreadNotifCount > 0)
                                            Positioned(
                                              right: -6,
                                              top: -6,
                                              child: Container(
                                                padding:
                                                    const EdgeInsets.all(4),
                                                decoration: const BoxDecoration(
                                                  color: AppTheme.accent,
                                                  shape: BoxShape.circle,
                                                ),
                                                constraints:
                                                    const BoxConstraints(
                                                        minWidth: 18,
                                                        minHeight: 18),
                                                child: Center(
                                                  child: Text(
                                                    _unreadNotifCount > 9
                                                        ? '9+'
                                                        : '$_unreadNotifCount',
                                                    style: const TextStyle(
                                                        color: Colors.white,
                                                        fontSize: 10,
                                                        fontWeight:
                                                            FontWeight.bold),
                                                  ),
                                                ),
                                              ),
                                            ),
                                        ],
                                      ),
                                    ),
                                  ),
                                  const SizedBox(width: 8),
                                  GestureDetector(
                                    onTap: () => Navigator.push(
                                        context,
                                        MaterialPageRoute(
                                            builder: (_) =>
                                                const ProfileScreen())),
                                    child: NeuContainer(
                                      padding: const EdgeInsets.all(10),
                                      shape: BoxShape.circle,
                                      child: const Icon(Icons.person,
                                          color: AppTheme.primary, size: 20),
                                    ),
                                  ),
                                  const SizedBox(width: 8),
                                  // More Menu (About, Logout)
                                  PopupMenuButton<String>(
                                    onSelected: (value) {
                                      switch (value) {
                                        case 'about':
                                          Navigator.push(
                                              context,
                                              MaterialPageRoute(
                                                  builder: (_) =>
                                                      const AboutScreen()));
                                          break;
                                        case 'logout':
                                          auth.logout();
                                          break;
                                      }
                                    },
                                    color: AppTheme.surface,
                                    shape: RoundedRectangleBorder(
                                        borderRadius: BorderRadius.circular(16),
                                        side: const BorderSide(
                                            color: Colors.white10)),
                                    icon: NeuContainer(
                                      padding: const EdgeInsets.all(10),
                                      shape: BoxShape.circle,
                                      child: const Icon(Icons.more_vert,
                                          color: AppTheme.primary, size: 20),
                                    ),
                                    itemBuilder: (context) => [
                                      const PopupMenuItem(
                                          value: 'about',
                                          child: Row(children: [
                                            Icon(Icons.info_outline,
                                                color: AppTheme.secondary,
                                                size: 18),
                                            SizedBox(width: 12),
                                            Text('Về ứng dụng',
                                                style: TextStyle(
                                                    color:
                                                        AppTheme.textPrimary))
                                          ])),
                                      const PopupMenuDivider(),
                                      const PopupMenuItem(
                                          value: 'logout',
                                          child: Row(children: [
                                            Icon(Icons.logout,
                                                color: AppTheme.accent,
                                                size: 18),
                                            SizedBox(width: 12),
                                            Text('Đăng xuất',
                                                style: TextStyle(
                                                    color: AppTheme.accent))
                                          ])),
                                    ],
                                  ),
                                ],
                              ).animate().fadeIn(duration: 200.ms),
                            ],
                          ),
                        ),

                        // ====== GREETING ======
                        Padding(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 24, vertical: 16),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                _getGreeting(),
                                style: Theme.of(context)
                                    .textTheme
                                    .bodyMedium
                                    ?.copyWith(
                                      color: AppTheme.secondary,
                                      fontWeight: FontWeight.bold,
                                      letterSpacing: 1,
                                    ),
                              ).animate().fadeIn(delay: 100.ms),
                              const SizedBox(height: 4),
                              Row(
                                children: [
                                  Expanded(
                                    child: Column(
                                      crossAxisAlignment:
                                          CrossAxisAlignment.start,
                                      children: [
                                        Text(
                                          userName,
                                          style: Theme.of(context)
                                              .textTheme
                                              .displayLarge
                                              ?.copyWith(fontSize: 28),
                                          maxLines: 1,
                                          overflow: TextOverflow.ellipsis,
                                        ).animate().fadeIn(delay: 150.ms),
                                        if (!isAdmin)
                                          Padding(
                                            padding:
                                                const EdgeInsets.only(top: 4),
                                            child: Text(
                                              "${auth.user?.mssv ?? ''} - ${auth.user?.lopName ?? 'Không có lớp'}",
                                              style: TextStyle(
                                                color: AppTheme.textMuted,
                                                fontSize: 14,
                                                fontWeight: FontWeight.w500,
                                              ),
                                            ).animate().fadeIn(delay: 200.ms),
                                          ),
                                      ],
                                    ),
                                  ),
                                  if (auth.isOfflineMode)
                                    Padding(
                                      padding: const EdgeInsets.only(left: 12),
                                      child: NeuContainer(
                                        padding: const EdgeInsets.symmetric(
                                            horizontal: 12, vertical: 6),
                                        borderRadius: 12,
                                        child: const Row(
                                          mainAxisSize: MainAxisSize.min,
                                          children: [
                                            Icon(Icons.cloud_off,
                                                color: AppTheme.warning,
                                                size: 12),
                                            SizedBox(width: 4),
                                            Text('Offline',
                                                style: TextStyle(
                                                    color: AppTheme.warning,
                                                    fontSize: 10,
                                                    fontWeight:
                                                        FontWeight.bold)),
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
                          child: _buildStatsGrid(attendance, isAdmin)
                              .animate()
                              .fadeIn(delay: 150.ms),
                        ),

                        const SizedBox(height: 32),

                        // ====== MAIN ACTIONS ======
                        Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 24),
                          child: _buildMainActions(isAdmin, auth.isOfflineMode)
                              .animate()
                              .fadeIn(delay: 200.ms),
                        ),

                        const SizedBox(height: 32),
                        // Mở rộng thêm sau này nếu cần
                        const SizedBox(height: 16),

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
  Widget _buildSyncBanner(
      ConnectivityProvider connectivity, AuthProvider auth) {
    if (connectivity.isOnline &&
        connectivity.pendingSyncCount == 0 &&
        !connectivity.isSyncing &&
        !auth.isOfflineMode) {
      return const SizedBox.shrink();
    }

    Color glowColor;
    IconData icon;
    String message;

    if (!connectivity.isOnline) {
      glowColor = AppTheme.error;
      icon = Icons.cloud_off;
      message = 'Offline';
      if (connectivity.pendingSyncCount > 0) {
        message += ' • ${connectivity.pendingSyncCount} pending';
      }
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
      onTap: () => Navigator.push(
          context, MaterialPageRoute(builder: (_) => const SyncStatusScreen())),
      child: NeuContainer(
        margin: const EdgeInsets.fromLTRB(24, 0, 24, 16),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        borderRadius: 16,
        child: Row(
          children: [
            if (connectivity.isSyncing)
              SizedBox(
                width: 16,
                height: 16,
                child:
                    CircularProgressIndicator(color: glowColor, strokeWidth: 2),
              )
            else
              Icon(icon, color: glowColor, size: 16),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                message,
                style: TextStyle(
                    color: glowColor,
                    fontSize: 13,
                    fontWeight: FontWeight.w600),
              ),
            ),
            if (connectivity.isOnline &&
                connectivity.pendingSyncCount > 0 &&
                !connectivity.isSyncing)
              GestureDetector(
                onTap: () => connectivity.manualSync(),
                child: Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  decoration: BoxDecoration(
                    color: glowColor.withValues(alpha: 0.2),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text('SYNC NOW',
                      style: TextStyle(
                          color: glowColor,
                          fontSize: 10,
                          fontWeight: FontWeight.bold,
                          letterSpacing: 1)),
                ),
              ),
            if (!connectivity.isOnline)
              Icon(Icons.chevron_right,
                  color: glowColor.withValues(alpha: 0.8), size: 18),
          ],
        ),
      ),
    ).animate().fadeIn().slideY(begin: -0.5, end: 0);
  }

  // ====== Stats Grid ======
  Widget _buildStatsGrid(AttendanceProvider attendance, bool isAdmin) {
    if (attendance.isLoading && attendance.stats == null) {
      return const Center(
          child: CircularProgressIndicator(color: AppTheme.secondary));
    }

    final stats = attendance.stats;
    return Column(
      children: [
        Row(
          children: [
            Expanded(
              child: _buildGlassStatCard(
                title: isAdmin ? "Tổng SV" : "Tổng Số Phiên",
                value: "${stats?.total ?? 0}",
                icon: isAdmin ? Icons.people_alt : Icons.class_,
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
          ],
        ),
        const SizedBox(height: 12),
        Row(
          children: [
            if (!isAdmin) ...[
              Expanded(
                child: _buildGlassStatCard(
                  title: "Đi trễ",
                  value: "${stats?.late ?? 0}",
                  icon: Icons.watch_later_outlined,
                  color: AppTheme.warning,
                ),
              ),
              const SizedBox(width: 12),
            ],
            Expanded(
              child: _buildGlassStatCard(
                title: "Vắng",
                value: "${stats?.absent ?? 0}",
                icon: Icons.person_off,
                color: AppTheme.error,
              ),
            ),
            if (!isAdmin) ...[
              const SizedBox(width: 12),
              Expanded(
                child: _buildGlassStatCard(
                  title: "Tỷ lệ",
                  value: "${stats?.rate ?? 0}%",
                  icon: Icons.percent,
                  color: AppTheme.secondary,
                ),
              ),
            ],
          ],
        ),
      ],
    );
  }

  Widget _buildGlassStatCard(
      {required String title,
      required String value,
      required IconData icon,
      required Color color}) {
    return NeuContainer(
      padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 12),
      borderRadius: 20,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: color, size: 28),
          const SizedBox(height: 12),
          Text(value,
              style: TextStyle(
                  color: Theme.of(context).textTheme.displayLarge?.color,
                  fontSize: 24,
                  fontWeight: FontWeight.bold)),
          const SizedBox(height: 4),
          Text(title,
              style: TextStyle(
                  color: Theme.of(context).textTheme.bodyMedium?.color,
                  fontSize: 12)),
        ],
      ),
    );
  }

  // ====== Tùy chọn mở rộng ======
  Widget _buildMainActions(bool isAdmin, bool isOffline) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          "Tính năng chính",
          style: TextStyle(
              color: Theme.of(context).textTheme.displayLarge?.color,
              fontSize: 18,
              fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 16),
        Row(
          children: [
            if (isAdmin) ...[
              Expanded(
                child: _buildActionCard(
                  title: "Thêm Face",
                  subtitle: "Đăng ký khuôn mặt",
                  icon: Icons.person_add,
                  gradient: const [Color(0xFF8B5CF6), Color(0xFF6D28D9)],
                  onTap: () => Navigator.push(
                      context,
                      MaterialPageRoute(
                          builder: (_) => const reg_screen.RegisterScreen())),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _buildActionCard(
                  title: "Tạo Phiên",
                  subtitle: "Phiên điểm danh",
                  icon: Icons.event,
                  gradient: const [AppTheme.secondary, AppTheme.primary],
                  onTap: () => Navigator.push(
                      context,
                      MaterialPageRoute(
                          builder: (_) => const AdminSessionScreen())),
                ),
              ),
            ] else ...[
              Expanded(
                child: _buildActionCard(
                  title: "Lịch Học",
                  subtitle: "Thời khóa biểu",
                  icon: Icons.calendar_today,
                  gradient: const [Color(0xFF8B5CF6), Color(0xFF6D28D9)],
                  onTap: () => Navigator.push(
                      context,
                      MaterialPageRoute(
                          builder: (_) => const ScheduleScreen())),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _buildActionCard(
                  title: "Quét QR",
                  subtitle: "Quét mã điểm danh",
                  icon: Icons.qr_code_scanner,
                  gradient: const [Color(0xFFF59E0B), Color(0xFFB45309)],
                  onTap: () => Navigator.push(
                      context,
                      MaterialPageRoute(
                          builder: (_) => const StudentQRScannerScreen())),
                ),
              ),
            ]
          ],
        ),
        if (!isAdmin) ...[
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: _buildActionCard(
                  title: "Lịch Sử",
                  subtitle: "Lịch sử điểm danh",
                  icon: Icons.history,
                  gradient: const [AppTheme.secondary, AppTheme.primary],
                  onTap: () {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(
                          content: Text('Tính năng đang phát triển')),
                    );
                  },
                ),
              ),
              const SizedBox(width: 12),
              const Expanded(child: SizedBox()), // Empty slot for balance
            ],
          ),
        ],
        if (!isAdmin) ...[
          const SizedBox(height: 24),
          Text(
            "Kết quả điểm danh gần nhất",
            style: TextStyle(
                color: Theme.of(context).textTheme.displayLarge?.color,
                fontSize: 18,
                fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 16),
          Consumer<AttendanceProvider>(
            builder: (context, attendance, child) {
              if (attendance.history.isEmpty) {
                return const Text("Chưa có dữ liệu",
                    style: TextStyle(color: AppTheme.textMuted));
              }
              final lastRecord = attendance.history.first;
              return NeuContainer(
                padding: const EdgeInsets.all(16),
                borderRadius: 16,
                child: Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: lastRecord.trangThai.toUpperCase() == 'PRESENT'
                            ? AppTheme.success.withValues(alpha: 0.1)
                            : (lastRecord.trangThai.toUpperCase() == 'LATE'
                                ? AppTheme.warning.withValues(alpha: 0.1)
                                : AppTheme.error.withValues(alpha: 0.1)),
                        shape: BoxShape.circle,
                      ),
                      child: Icon(
                        lastRecord.trangThai.toUpperCase() == 'PRESENT'
                            ? Icons.check_circle
                            : (lastRecord.trangThai.toUpperCase() == 'LATE'
                                ? Icons.watch_later
                                : Icons.cancel),
                        color: lastRecord.trangThai.toUpperCase() == 'PRESENT'
                            ? AppTheme.success
                            : (lastRecord.trangThai.toUpperCase() == 'LATE'
                                ? AppTheme.warning
                                : AppTheme.error),
                      ),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(lastRecord.thoiGian,
                              style: const TextStyle(
                                  fontWeight: FontWeight.bold, fontSize: 16)),
                          Text("Giờ ra: ${lastRecord.gioRa ?? '--:--'}",
                              style: const TextStyle(
                                  color: AppTheme.textMuted, fontSize: 12)),
                        ],
                      ),
                    ),
                    Text(
                      lastRecord.trangThai.toUpperCase() == 'PRESENT'
                          ? 'Có mặt'
                          : (lastRecord.trangThai.toUpperCase() == 'LATE'
                              ? 'Đi trễ'
                              : 'Vắng'),
                      style: TextStyle(
                        color: lastRecord.trangThai.toUpperCase() == 'PRESENT'
                            ? AppTheme.success
                            : (lastRecord.trangThai.toUpperCase() == 'LATE'
                                ? AppTheme.warning
                                : AppTheme.error),
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
              );
            },
          ),
        ],
        if (isAdmin) ...[
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: _buildActionCard(
                  title: "Thống Kê",
                  subtitle: "Báo cáo Admin",
                  icon: Icons.bar_chart,
                  gradient: const [Color(0xFF3B82F6), Color(0xFF1D4ED8)],
                  onTap: () => Navigator.push(
                      context,
                      MaterialPageRoute(
                          builder: (_) => const AdminStatsScreen())),
                ),
              ),
              const SizedBox(width: 12),
              const Expanded(child: SizedBox()), // Nút QR cũ đã chuyển qua sinh viên
            ],
          ),
        ],
      ],
    );
  }

  Widget _buildActionCard(
      {required String title,
      required String subtitle,
      required IconData icon,
      required List<Color> gradient,
      required VoidCallback onTap}) {
    return GestureDetector(
      onTap: onTap,
      child: NeuContainer(
        padding: const EdgeInsets.all(16),
        borderRadius: 20,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  gradient: LinearGradient(
                    colors: gradient,
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  boxShadow: [
                    BoxShadow(
                      color: gradient.first.withOpacity(0.4),
                      blurRadius: 12,
                      offset: const Offset(0, 4),
                    )
                  ]),
              child: Icon(icon, color: Colors.white, size: 28),
            ),
            const SizedBox(height: 16),
            Text(title,
                style: TextStyle(
                    color: Theme.of(context).textTheme.displayLarge?.color,
                    fontSize: 16,
                    fontWeight: FontWeight.bold)),
            const SizedBox(height: 4),
            Text(subtitle,
                style: TextStyle(
                    color: Theme.of(context).textTheme.bodyMedium?.color,
                    fontSize: 12)),
          ],
        ),
      ),
    );
  }
}
