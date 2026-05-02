import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/attendance_provider.dart';
import '../providers/auth_provider.dart';
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
import '../services/export_service.dart';
import '../services/api_service.dart';

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
    if (hour < 12) return "Chào buổi sáng";
    if (hour < 18) return "Chào buổi chiều";
    return "Chào buổi tối";
  }

  @override
  Widget build(BuildContext context) {
    final auth = Provider.of<AuthProvider>(context);
    final attendance = Provider.of<AttendanceProvider>(context);
    final isAdmin = auth.user?.role != 'student';
    final userName = auth.user?.name ?? 'Admin';

    return Scaffold(
      backgroundColor: const Color(0xFFF0F4F8),
      body: SafeArea(
        child: RefreshIndicator(
          color: const Color(0xFF1B3A5C),
          onRefresh: () => attendance.fetchDashboardData(),
          child: SingleChildScrollView(
            physics: const AlwaysScrollableScrollPhysics(),
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const SizedBox(height: 20),

                  // ====== TOP BAR ======
                  LayoutBuilder(
                    builder: (context, constraints) {
                      bool isNarrow = constraints.maxWidth < 300;
                      return Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          // Logo
                          Flexible(
                            child: Row(
                              mainAxisSize: MainAxisSize.min,
                               children: [
                                 Container(
                                  padding: const EdgeInsets.all(4),
                                  decoration: BoxDecoration(
                                    color: Colors.white,
                                    borderRadius: BorderRadius.circular(10),
                                    boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 5)],
                                  ),
                                  child: Image.asset(
                                    "assets/images/logo_MTU.png", 
                                    width: 32, 
                                    height: 32,
                                    errorBuilder: (context, error, stackTrace) => const Icon(Icons.face_retouching_natural, color: Color(0xFF1B3A5C), size: 22),
                                  ),
                                ),
                                if (!isNarrow) ...[
                                   const SizedBox(width: 10),
                                   const Text("MTU FACE", style: TextStyle(color: Color(0xFF1B3A5C), fontWeight: FontWeight.bold, fontSize: 16)),
                                ],
                               ],
                            ),
                          ),
                          // Actions
                          Flexible(
                            child: Row(
                              mainAxisAlignment: MainAxisAlignment.end,
                              children: [
                                if (isAdmin && !isNarrow)
                                  Flexible(
                                    child: Container(
                                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                                      decoration: BoxDecoration(
                                        color: const Color(0xFF1B3A5C).withOpacity(0.08),
                                        borderRadius: BorderRadius.circular(10),
                                      ),
                                      child: const Row(
                                        mainAxisSize: MainAxisSize.min,
                                        children: [
                                          Icon(Icons.admin_panel_settings, color: Color(0xFF1B3A5C), size: 14),
                                          SizedBox(width: 4),
                                          Flexible(child: Text("Admin", overflow: TextOverflow.ellipsis, style: TextStyle(color: Color(0xFF1B3A5C), fontSize: 11, fontWeight: FontWeight.w600))),
                                        ],
                                      ),
                                    ),
                                  ),
                                const SizedBox(width: 8),
                                GestureDetector(
                                  onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const ProfileScreen())),
                                  child: Container(
                                    padding: const EdgeInsets.all(10),
                                    decoration: BoxDecoration(
                                      color: const Color(0xFF1B3A5C).withOpacity(0.08),
                                      borderRadius: BorderRadius.circular(12),
                                    ),
                                    child: const Icon(Icons.person_outline, color: Color(0xFF1B3A5C), size: 20),
                                  ),
                                ),
                                if (!isNarrow) ...[
                                    const SizedBox(width: 8),
                                    GestureDetector(
                                      onTap: () => auth.logout(),
                                      child: Container(
                                        padding: const EdgeInsets.all(10),
                                        decoration: BoxDecoration(
                                          color: const Color(0xFF1B3A5C).withOpacity(0.08),
                                          borderRadius: BorderRadius.circular(12),
                                        ),
                                        child: const Icon(Icons.logout, color: Color(0xFF1B3A5C), size: 20),
                                      ),
                                    ),
                                ],
                              ],
                            ),
                          ),
                        ],
                      );
                    },
                  ),

                  const SizedBox(height: 28),

                  // ====== GREETING ======
                  Text(
                    "Xin chào, $userName!",
                    style: const TextStyle(fontSize: 26, fontWeight: FontWeight.bold, color: Color(0xFF1B3A5C)),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    _getGreeting(),
                    style: TextStyle(fontSize: 14, color: const Color(0xFF1B3A5C).withOpacity(0.5)),
                  ),

                  const SizedBox(height: 24),

                  // ====== WELCOME CARD (Navy) ======
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(22),
                    decoration: BoxDecoration(
                      gradient: const LinearGradient(
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                        colors: [Color(0xFF1B3A5C), Color(0xFF2A5298)],
                      ),
                      borderRadius: BorderRadius.circular(20),
                      boxShadow: [
                        BoxShadow(color: const Color(0xFF1B3A5C).withOpacity(0.3), blurRadius: 20, offset: const Offset(0, 8)),
                      ],
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            // Avatar
                            Container(
                              width: 48,
                              height: 48,
                              decoration: BoxDecoration(
                                shape: BoxShape.circle,
                                color: Colors.white.withOpacity(0.2),
                                border: Border.all(color: Colors.white.withOpacity(0.4), width: 2),
                              ),
                              child: Center(
                                child: Text(
                                  userName[0].toUpperCase(),
                                  style: const TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold),
                                ),
                              ),
                            ),
                            const SizedBox(width: 14),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  const Text("Tổng quan hôm nay", style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.w600)),
                                  Text("Hệ thống điểm danh AI", style: TextStyle(color: Colors.white.withOpacity(0.6), fontSize: 12)),
                                ],
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 20),
                        // Stats row
                        Row(
                          children: [
                            Expanded(child: _buildNavyStat("Sĩ số", "${attendance.stats?.total ?? '--'}")),
                            Container(width: 1, height: 36, color: Colors.white.withOpacity(0.2)),
                            Expanded(child: _buildNavyStat("Có mặt", "${attendance.stats?.present ?? '--'}")),
                            Container(width: 1, height: 36, color: Colors.white.withOpacity(0.2)),
                            Expanded(child: _buildNavyStat("Vắng", "${attendance.stats?.absent ?? '--'}")),
                          ],
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 28),

                  // ====== CHỨC NĂNG ======
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Expanded(child: Text("Chức năng", style: TextStyle(fontSize: 17, fontWeight: FontWeight.bold, color: Color(0xFF1B3A5C)))),
                      GestureDetector(
                        onTap: () => setState(() => _isFeaturesExpanded = !(_isFeaturesExpanded ?? false)),
                        child: Text(
                          (_isFeaturesExpanded ?? false) ? "Thu gọn" : "Xem tất cả", 
                          style: TextStyle(fontSize: 13, color: (_isFeaturesExpanded ?? false) ? const Color(0xFF10B981) : const Color(0xFF1B3A5C).withOpacity(0.4), fontWeight: (_isFeaturesExpanded ?? false) ? FontWeight.bold : FontWeight.normal)
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 14),

                  // Feature Grid
                  if (isAdmin)
                    Column(
                      children: [
                        Row(
                          children: [
                            Expanded(
                              child: _buildFeatureCard(
                                icon: Icons.event_available,
                                title: "Mở điểm danh",
                                subtitle: "Tạo phiên cho SV",
                                iconBgColor: const Color(0xFF10B981),
                                onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const AdminSessionScreen())),
                              ),
                            ),
                            const SizedBox(width: 14),
                            Expanded(
                              child: _buildFeatureCard(
                                icon: Icons.face_retouching_natural,
                                title: "Quét mặt",
                                subtitle: "Camera AI",
                                iconBgColor: const Color(0xFF2E96EB),
                                onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const scan_screen.ScanScreen())),
                              ),
                            ),
                          ],
                        ),
                        if (_isFeaturesExpanded) ...[
                          const SizedBox(height: 14),
                          Row(
                            children: [
                              Expanded(
                                child: _buildFeatureCard(
                                  icon: Icons.person_add_alt_1,
                                  title: "Đăng ký",
                                  subtitle: "Khuôn mặt mới",
                                  iconBgColor: const Color(0xFF6366F1),
                                  onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const reg_screen.RegisterScreen())),
                                ),
                              ),
                              const SizedBox(width: 14),
                              Expanded(
                                child: _buildFeatureCard(
                                  icon: Icons.fact_check_outlined,
                                  title: "Duyệt ảnh",
                                  subtitle: "Xác minh SV",
                                  iconBgColor: const Color(0xFFF59E0B),
                                  onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const FaceApprovalScreen())),
                                ),
                              ),
                            ],
                          ),
                          Row(
                            children: [
                              Expanded(
                                child: _buildFeatureCard(
                                  icon: Icons.history,
                                  title: "Lịch sử ĐD",
                                  subtitle: "Phiên đã đóng",
                                  iconBgColor: const Color(0xFF8B5CF6),
                                  onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const SessionHistoryScreen())),
                                ),
                              ),
                              const SizedBox(width: 14),
                              Expanded(
                                child: _buildFeatureCard(
                                  icon: Icons.bar_chart_rounded,
                                  title: "Thống kê",
                                  subtitle: "Biểu đồ & Phân tích",
                                  iconBgColor: const Color(0xFFEC4899),
                                  onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const AdminStatsScreen())),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 14),
                          Row(
                            children: [
                              Expanded(
                                child: _buildFeatureCard(
                                  icon: Icons.notifications_rounded,
                                  title: "Thông báo",
                                  subtitle: "Gửi & Xem tin",
                                  iconBgColor: const Color(0xFFF59E0B),
                                  onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const NotificationsScreen())),
                                ),
                              ),
                              const SizedBox(width: 14),
                              const Expanded(child: SizedBox()),
                            ],
                          ),
                        ],
                      ],
                    )
                  else
                    Column(
                      children: [
                        Row(
                          children: [
                            Expanded(
                              child: _buildFeatureCard(
                                icon: Icons.qr_code_scanner,
                                title: "Điểm danh QR",
                                subtitle: "Quét lớp học",
                                iconBgColor: const Color(0xFF10B981),
                                onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const StudentQRScannerScreen())),
                              ),
                            ),
                            const SizedBox(width: 14),
                            Expanded(
                              child: _buildFeatureCard(
                                icon: Icons.person_add_alt_1,
                                title: "Đăng ký",
                                subtitle: "Cập nhật ảnh",
                                iconBgColor: const Color(0xFF2E96EB),
                                onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const reg_screen.RegisterScreen())),
                              ),
                            ),
                          ],
                        ),
                        if (_isFeaturesExpanded) ...[
                          const SizedBox(height: 14),
                          Row(
                            children: [
                              Expanded(
                                child: _buildFeatureCard(
                                  icon: Icons.calendar_month_outlined,
                                  title: "Lịch học",
                                  subtitle: "Thời khóa biểu",
                                  iconBgColor: const Color(0xFFF59E0B),
                                  onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const ScheduleScreen())),
                                ),
                              ),
                              const SizedBox(width: 14),
                              Expanded(
                                child: _buildFeatureCard(
                                  icon: Icons.notifications_rounded,
                                  title: "Thông báo",
                                  subtitle: "Cảnh báo vắng",
                                  iconBgColor: const Color(0xFFF59E0B),
                                  onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const NotificationsScreen())),
                                ),
                              ),
                            ],
                          ),
                        ],
                      ],
                    ),

                  const SizedBox(height: 28),

                  // ====== LỊCH SỬ ======
                  GestureDetector(
                    onTap: () => setState(() => _isHistoryCollapsed = !_isHistoryCollapsed),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Expanded(
                          child: Row(children: [
                            Icon(
                              _isHistoryCollapsed ? Icons.keyboard_arrow_right : Icons.keyboard_arrow_down,
                              color: const Color(0xFF1B3A5C), size: 20,
                            ),
                            const SizedBox(width: 4),
                            const Text("Hoạt động gần đây",
                              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Color(0xFF1B3A5C), overflow: TextOverflow.ellipsis)
                            ),
                          ]),
                        ),
                        const SizedBox(width: 8),
                        Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            if (isAdmin && attendance.history.isNotEmpty)
                              GestureDetector(
                                onTap: () => _confirmClearAll(attendance),
                                child: Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                  margin: const EdgeInsets.only(right: 6),
                                  decoration: BoxDecoration(
                                    color: Colors.redAccent.withOpacity(0.1),
                                    borderRadius: BorderRadius.circular(8),
                                  ),
                                  child: const Row(
                                    children: [
                                      Icon(Icons.delete_sweep, color: Colors.redAccent, size: 12),
                                      SizedBox(width: 4),
                                      Text("Xóa hết", style: TextStyle(color: Colors.redAccent, fontSize: 10, fontWeight: FontWeight.bold)),
                                    ],
                                  ),
                                ),
                              ),
                            if (isAdmin)
                              GestureDetector(
                                onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const HistoryReportScreen())),
                                child: Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                  margin: const EdgeInsets.only(right: 6),
                                  decoration: BoxDecoration(
                                    color: const Color(0xFF10B981).withOpacity(0.1),
                                    borderRadius: BorderRadius.circular(8),
                                    border: Border.all(color: const Color(0xFF10B981).withOpacity(0.2)),
                                  ),
                                  child: const Row(
                                    children: [
                                      Icon(Icons.filter_list, color: Color(0xFF10B981), size: 12),
                                      SizedBox(width: 4),
                                      Text("Lọc", style: TextStyle(color: Color(0xFF10B981), fontSize: 10, fontWeight: FontWeight.bold)),
                                    ],
                                  ),
                                ),
                              ),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                              decoration: BoxDecoration(
                                color: const Color(0xFF1B3A5C).withOpacity(0.08),
                                borderRadius: BorderRadius.circular(8),
                              ),
                              child: Text(
                                "${attendance.history.length}",
                                style: const TextStyle(color: Color(0xFF1B3A5C), fontSize: 11, fontWeight: FontWeight.w600),
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 14),

                  // History list (collapsible)
                  if (!_isHistoryCollapsed) ...[
                    if (attendance.isLoading)
                      const Padding(
                        padding: EdgeInsets.symmetric(vertical: 40),
                        child: Center(child: CircularProgressIndicator(color: Color(0xFF1B3A5C))),
                      )
                    else if (attendance.history.isEmpty)
                      _buildEmptyState()
                    else
                      ...attendance.history.map((record) => _buildHistoryItem(record, isAdmin, attendance)),
                  ],

                  const SizedBox(height: 24),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  // ====== Navy Stat ======
  Widget _buildNavyStat(String label, String value) {
    return Column(
      children: [
        Text(value, style: const TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.bold)),
        const SizedBox(height: 4),
        Text(label, style: TextStyle(color: Colors.white.withOpacity(0.6), fontSize: 12)),
      ],
    );
  }

  // ====== Feature Card ======
  Widget _buildFeatureCard({
    required IconData icon,
    required String title,
    required String subtitle,
    required Color iconBgColor,
    required VoidCallback onTap,
  }) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(18),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(18),
          boxShadow: [
            BoxShadow(color: Colors.black.withOpacity(0.04), blurRadius: 12, offset: const Offset(0, 4)),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Icon
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: iconBgColor.withOpacity(0.12),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Icon(icon, color: iconBgColor, size: 24),
            ),
            const SizedBox(height: 14),
            Text(title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: Color(0xFF1B3A5C))),
            const SizedBox(height: 4),
            Text(subtitle, style: TextStyle(fontSize: 12, color: const Color(0xFF1B3A5C).withOpacity(0.4))),
            const SizedBox(height: 12),
            // Progress bar giả lập
            ClipRRect(
              borderRadius: BorderRadius.circular(4),
              child: LinearProgressIndicator(
                value: 0.7,
                backgroundColor: iconBgColor.withOpacity(0.08),
                color: iconBgColor,
                minHeight: 5,
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ====== Empty State ======
  Widget _buildEmptyState() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(vertical: 40),
      child: Column(
        children: [
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: const Color(0xFF1B3A5C).withOpacity(0.06),
              shape: BoxShape.circle,
            ),
            child: const Icon(Icons.inbox_rounded, color: Color(0xFF1B3A5C), size: 40),
          ),
          const SizedBox(height: 16),
          const Text("Chưa có dữ liệu", style: TextStyle(color: Color(0xFF94A3B8), fontSize: 15, fontWeight: FontWeight.w500)),
          const SizedBox(height: 4),
          Text("Bắt đầu điểm danh để xem kết quả", style: TextStyle(color: const Color(0xFF1B3A5C).withOpacity(0.3), fontSize: 12)),
        ],
      ),
    );
  }

  // ====== History Item (with swipe-to-delete for Admin) ======
  Widget _buildHistoryItem(dynamic record, bool isAdmin, AttendanceProvider attendance) {
    final Widget card = Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(color: Colors.black.withOpacity(0.03), blurRadius: 8, offset: const Offset(0, 2)),
        ],
      ),
      child: Row(
        children: [
          // Avatar
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: const Color(0xFF1B3A5C).withOpacity(0.08),
            ),
            child: const Icon(Icons.person, color: Color(0xFF1B3A5C), size: 22),
          ),
          const SizedBox(width: 14),
          // Info
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(record.hoTen, 
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(fontWeight: FontWeight.w600, color: Color(0xFF1B3A5C), fontSize: 14.5)
                ),
                const SizedBox(height: 3),
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                      decoration: BoxDecoration(
                        color: const Color(0xFF1B3A5C).withOpacity(0.06),
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: Text(record.mssv, style: const TextStyle(fontSize: 10, color: Color(0xFF1B3A5C), fontWeight: FontWeight.w500)),
                    ),
                    const SizedBox(width: 6),
                    Text("• ${record.maLop}", style: TextStyle(fontSize: 11, color: const Color(0xFF1B3A5C).withOpacity(0.4))),
                  ],
                ),
              ],
            ),
          ),
          // Time + Status
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                record.thoiGian.split(' ')[1],
                style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: Color(0xFF1B3A5C)),
              ),
              const SizedBox(height: 4),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: const Color(0xFF10B981).withOpacity(0.1),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Text("Hợp lệ", style: TextStyle(fontSize: 10, color: Color(0xFF10B981), fontWeight: FontWeight.bold)),
              ),
            ],
          ),
        ],
      ),
    );

    // Admin: Vuốt sang trái để xóa
    if (isAdmin && record.id != null) {
      return Dismissible(
        key: Key('record_${record.id}'),
        direction: DismissDirection.endToStart,
        background: Container(
          margin: const EdgeInsets.only(bottom: 10),
          padding: const EdgeInsets.only(right: 20),
          alignment: Alignment.centerRight,
          decoration: BoxDecoration(
            color: Colors.redAccent,
            borderRadius: BorderRadius.circular(16),
          ),
          child: const Icon(Icons.delete, color: Colors.white),
        ),
        confirmDismiss: (direction) async {
          return await showDialog<bool>(
            context: context,
            builder: (ctx) => AlertDialog(
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
              title: const Text('Xóa bản ghi này?'),
              content: Text('Xóa điểm danh của ${record.hoTen}?'),
              actions: [
                TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Hủy')),
                ElevatedButton(
                  onPressed: () => Navigator.pop(ctx, true),
                  style: ElevatedButton.styleFrom(backgroundColor: Colors.redAccent, foregroundColor: Colors.white),
                  child: const Text('Xóa'),
                ),
              ],
            ),
          );
        },
        onDismissed: (_) => _deleteRecord(record.id, attendance),
        child: card,
      );
    }

    return card;
  }

  Future<void> _deleteRecord(int recordId, AttendanceProvider attendance) async {
    try {
      final result = await _api.deleteAttendanceRecord(recordId);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text(result['message'] ?? 'Đã xóa'),
          backgroundColor: result['success'] == true ? Colors.green : Colors.red,
          duration: const Duration(seconds: 2),
        ));
        attendance.fetchDashboardData();
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Lỗi: $e'), backgroundColor: Colors.red));
      }
    }
  }

  Future<void> _confirmClearAll(AttendanceProvider attendance) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Row(children: [
          Icon(Icons.warning_amber_rounded, color: Colors.redAccent, size: 28),
          SizedBox(width: 8),
          Text('Xóa tất cả?'),
        ]),
        content: const Text('Thao tác này sẽ xóa TOÀN BỘ lịch sử điểm danh.\nHành động không thể hoàn tác!'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Hủy')),
          ElevatedButton(
            onPressed: () => Navigator.pop(ctx, true),
            style: ElevatedButton.styleFrom(backgroundColor: Colors.redAccent, foregroundColor: Colors.white),
            child: const Text('Xóa tất cả'),
          ),
        ],
      ),
    );

    if (confirm == true) {
      try {
        final result = await _api.clearAttendanceHistory();
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content: Text(result['message'] ?? 'Đã xóa'),
            backgroundColor: result['success'] == true ? Colors.green : Colors.red,
          ));
          attendance.fetchDashboardData();
        }
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Lỗi: $e'), backgroundColor: Colors.red));
        }
      }
    }
  }
}
