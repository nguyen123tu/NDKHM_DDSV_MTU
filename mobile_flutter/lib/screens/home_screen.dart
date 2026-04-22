import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/attendance_provider.dart';
import '../providers/auth_provider.dart';
import 'scan_screen.dart' as scan_screen;
import 'register_screen.dart' as reg_screen;

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  _HomeScreenState createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
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
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      // Logo
                      Container(
                        padding: const EdgeInsets.all(10),
                        decoration: BoxDecoration(
                          color: const Color(0xFF1B3A5C),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: const Icon(Icons.face_retouching_natural, color: Colors.white, size: 22),
                      ),
                      // Actions
                      Row(
                        children: [
                          if (isAdmin)
                            Container(
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
                                  Text("Admin", style: TextStyle(color: Color(0xFF1B3A5C), fontSize: 11, fontWeight: FontWeight.w600)),
                                ],
                              ),
                            ),
                          const SizedBox(width: 8),
                          GestureDetector(
                            onTap: () => auth.logout(),
                            child: Container(
                              padding: const EdgeInsets.all(10),
                              decoration: BoxDecoration(
                                color: Colors.red.withOpacity(0.08),
                                borderRadius: BorderRadius.circular(12),
                              ),
                              child: Icon(Icons.logout, color: Colors.red.withOpacity(0.7), size: 20),
                            ),
                          ),
                        ],
                      ),
                    ],
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
                            _buildNavyStat("Sĩ số", "${attendance.stats?.total ?? '--'}"),
                            Container(width: 1, height: 36, color: Colors.white.withOpacity(0.2)),
                            _buildNavyStat("Có mặt", "${attendance.stats?.present ?? '--'}"),
                            Container(width: 1, height: 36, color: Colors.white.withOpacity(0.2)),
                            _buildNavyStat("Vắng", "${attendance.stats?.absent ?? '--'}"),
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
                      const Text("Chức năng", style: TextStyle(fontSize: 17, fontWeight: FontWeight.bold, color: Color(0xFF1B3A5C))),
                      Text("Xem tất cả", style: TextStyle(fontSize: 13, color: const Color(0xFF1B3A5C).withOpacity(0.4))),
                    ],
                  ),
                  const SizedBox(height: 14),

                  // Feature Grid
                  if (isAdmin)
                    Row(
                      children: [
                        Expanded(
                          child: _buildFeatureCard(
                            icon: Icons.face_retouching_natural,
                            title: "Điểm danh",
                            subtitle: "Quét khuôn mặt",
                            iconBgColor: const Color(0xFF10B981),
                            onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const scan_screen.ScanScreen())),
                          ),
                        ),
                        const SizedBox(width: 14),
                        Expanded(
                          child: _buildFeatureCard(
                            icon: Icons.person_add_alt_1,
                            title: "Đăng ký",
                            subtitle: "Khuôn mặt mới",
                            iconBgColor: const Color(0xFF2E96EB),
                            onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const reg_screen.RegisterScreen())),
                          ),
                        ),
                      ],
                    )
                  else
                    _buildFeatureCard(
                      icon: Icons.person_add_alt_1,
                      title: "Đăng ký khuôn mặt",
                      subtitle: "Chụp ảnh để hệ thống nhận diện",
                      iconBgColor: const Color(0xFF2E96EB),
                      onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const reg_screen.RegisterScreen())),
                    ),

                  const SizedBox(height: 28),

                  // ====== LỊCH SỬ ======
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text("Hoạt động gần đây", style: TextStyle(fontSize: 17, fontWeight: FontWeight.bold, color: Color(0xFF1B3A5C))),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                        decoration: BoxDecoration(
                          color: const Color(0xFF1B3A5C).withOpacity(0.08),
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: Text(
                          "${attendance.history.length} bản ghi",
                          style: const TextStyle(color: Color(0xFF1B3A5C), fontSize: 11, fontWeight: FontWeight.w600),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 14),

                  // History list
                  if (attendance.isLoading)
                    const Padding(
                      padding: EdgeInsets.symmetric(vertical: 40),
                      child: Center(child: CircularProgressIndicator(color: Color(0xFF1B3A5C))),
                    )
                  else if (attendance.history.isEmpty)
                    _buildEmptyState()
                  else
                    ...attendance.history.map((record) => _buildHistoryItem(record)),

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
    return Expanded(
      child: Column(
        children: [
          Text(value, style: const TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.bold)),
          const SizedBox(height: 4),
          Text(label, style: TextStyle(color: Colors.white.withOpacity(0.6), fontSize: 12)),
        ],
      ),
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

  // ====== History Item ======
  Widget _buildHistoryItem(dynamic record) {
    return Container(
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
                Text(record.hoTen, style: const TextStyle(fontWeight: FontWeight.w600, color: Color(0xFF1B3A5C), fontSize: 14.5)),
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
  }
}
