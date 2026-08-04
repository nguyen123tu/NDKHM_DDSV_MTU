import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../services/api_service.dart';
import '../theme/app_theme.dart';
import '../widgets/neu_container.dart';

class AdminStatsScreen extends StatefulWidget {
  const AdminStatsScreen({super.key});

  @override
  State<AdminStatsScreen> createState() => _AdminStatsScreenState();
}

class _AdminStatsScreenState extends State<AdminStatsScreen> {
  final ApiService _api = ApiService();
  bool _isLoading = true;
  List<dynamic> _classStats = [];
  List<dynamic> _absentRisk = [];
  List<dynamic> _dailyTrend = [];

  @override
  void initState() {
    super.initState();
    _loadAllStats();
  }

  Future<void> _loadAllStats() async {
    setState(() => _isLoading = true);
    try {
      final results = await Future.wait([
        _api.getStatsClasses(),
        _api.getStatsAbsentRisk(),
        _api.getStatsDailyTrend(),
      ]);

      if (mounted) {
        setState(() {
          _classStats = results[0]['data'] ?? [];
          _absentRisk = results[1]['data'] ?? [];
          _dailyTrend = results[2]['data'] ?? [];
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  // ==== Logic Tính Toán Tổng Quan ====
  int get _totalClasses => _classStats.length;

  double get _avgAttendanceRate {
    if (_classStats.isEmpty) return 0.0;
    double totalPercent = 0.0;
    for (var c in _classStats) {
      final t = c['tong_sv'] ?? 0;
      final p = c['so_co_mat_hom_nay'] ?? 0;
      if (t > 0) totalPercent += (p / t);
    }
    return totalPercent / _classStats.length;
  }

  int get _totalRisk => _absentRisk.length;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      appBar: AppBar(
        title: const Text('Báo Cáo & Thống Kê',
            style: TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: Colors.transparent,
        foregroundColor: AppTheme.textPrimary,
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh, color: AppTheme.secondary),
            onPressed: _loadAllStats,
          ),
        ],
      ),
      body: Stack(
        children: [
          Container(color: Theme.of(context).scaffoldBackgroundColor),
          _isLoading
              ? const Center(
                  child: CircularProgressIndicator(color: AppTheme.secondary))
              : RefreshIndicator(
                  onRefresh: _loadAllStats,
                  color: AppTheme.secondary,
                  backgroundColor: AppTheme.surfaceLight,
                  child: SingleChildScrollView(
                    physics: const AlwaysScrollableScrollPhysics(),
                    padding: const EdgeInsets.all(20),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        // Thẻ tóm tắt tổng quan
                        _buildOverviewSummary()
                            .animate()
                            .fadeIn(duration: 300.ms)
                            .slideY(begin: 0.1),
                        const SizedBox(height: 32),

                        _buildSectionTitle("Xu Hướng Điểm Danh (7 ngày)"),
                        _buildTrendChart()
                            .animate()
                            .fadeIn(delay: 100.ms)
                            .slideY(begin: 0.1),
                        const SizedBox(height: 32),

                        _buildSectionTitle("Tỉ Lệ Đi Học Theo Lớp",
                            icon: Icons.class_),
                        _buildClassList()
                            .animate()
                            .fadeIn(delay: 200.ms)
                            .slideY(begin: 0.1),
                        const SizedBox(height: 32),

                        _buildSectionTitle("Cảnh Báo Vắng Nhiều",
                            icon: Icons.warning_amber_rounded,
                            color: AppTheme.error),
                        _buildAbsentRiskList()
                            .animate()
                            .fadeIn(delay: 300.ms)
                            .slideY(begin: 0.1),
                        const SizedBox(height: 40),
                      ],
                    ),
                  ),
                ),
        ],
      ),
    );
  }

  Widget _buildSectionTitle(String title,
      {IconData? icon, Color color = AppTheme.textPrimary}) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Row(
        children: [
          if (icon != null) ...[
            Icon(icon, color: color, size: 20),
            const SizedBox(width: 8),
          ],
          Text(title,
              style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                  color: color,
                  letterSpacing: 0.5)),
        ],
      ),
    );
  }

  // Thống kê tổng quan logic
  Widget _buildOverviewSummary() {
    return Row(
      children: [
        Expanded(
          child: _buildSummaryCard(
            title: "Lớp Đang Mở",
            value: "$_totalClasses",
            icon: Icons.layers,
            gradient: const [AppTheme.secondary, AppTheme.primary],
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: _buildSummaryCard(
            title: "Tỉ lệ TB",
            value: "${(_avgAttendanceRate * 100).toStringAsFixed(1)}%",
            icon: Icons.pie_chart,
            gradient: const [Color(0xFF10B981), Color(0xFF059669)], // Xanh lá
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: _buildSummaryCard(
            title: "Cảnh Báo",
            value: "$_totalRisk",
            icon: Icons.notifications_active,
            gradient: const [Color(0xFFEF4444), Color(0xFFB91C1C)], // Đỏ
          ),
        ),
      ],
    );
  }

  Widget _buildSummaryCard(
      {required String title,
      required String value,
      required IconData icon,
      required List<Color> gradient}) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: LinearGradient(
            colors: gradient,
            begin: Alignment.topLeft,
            end: Alignment.bottomRight),
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
              color: gradient.first.withValues(alpha: 0.3),
              blurRadius: 12,
              offset: const Offset(0, 4)),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: Colors.white.withValues(alpha: 0.8), size: 24),
          const SizedBox(height: 12),
          Text(value,
              style: const TextStyle(
                  color: Colors.white,
                  fontSize: 22,
                  fontWeight: FontWeight.bold)),
          const SizedBox(height: 4),
          Text(title,
              style: TextStyle(
                  color: Colors.white.withValues(alpha: 0.8), fontSize: 11)),
        ],
      ),
    );
  }

  Widget _buildTrendChart() {
    if (_dailyTrend.isEmpty) {
      return NeuContainer(
        height: 200,
        borderRadius: 20,
        child: const Center(
            child: Text("Không đủ dữ liệu xu hướng",
                style: TextStyle(color: AppTheme.textMuted))),
      );
    }

    // Lọc lại để tránh lỗi null / invalid format
    List<FlSpot> spots = [];
    for (int i = 0; i < _dailyTrend.length; i++) {
      double yVal = double.tryParse(_dailyTrend[i]['so_luong'].toString()) ?? 0;
      spots.add(FlSpot(i.toDouble(), yVal));
    }

    return NeuContainer(
      height: 240,
      padding: const EdgeInsets.only(top: 30, right: 20, left: 10, bottom: 10),
      borderRadius: 20,
      child: LineChart(
        LineChartData(
          gridData: FlGridData(
            show: true,
            drawVerticalLine: false,
            horizontalInterval: 1,
            getDrawingHorizontalLine: (value) {
              return FlLine(
                  color: Colors.white.withValues(alpha: 0.05), strokeWidth: 1);
            },
          ),
          titlesData: FlTitlesData(
            leftTitles: AxisTitles(
              sideTitles: SideTitles(
                showTitles: true,
                reservedSize: 30,
                getTitlesWidget: (value, meta) {
                  // Giấu số thập phân trên trục Y (ví dụ: 1.0 -> 1)
                  if (value % 1 != 0) return const SizedBox();
                  return Text(value.toInt().toString(),
                      style: const TextStyle(
                          color: AppTheme.textMuted, fontSize: 10));
                },
              ),
            ),
            topTitles:
                const AxisTitles(sideTitles: SideTitles(showTitles: false)),
            rightTitles:
                const AxisTitles(sideTitles: SideTitles(showTitles: false)),
            bottomTitles: AxisTitles(
              sideTitles: SideTitles(
                showTitles: true,
                getTitlesWidget: (value, meta) {
                  int index = value.toInt();
                  if (index >= 0 && index < _dailyTrend.length) {
                    return Padding(
                      padding: const EdgeInsets.only(top: 8),
                      child: Text(_dailyTrend[index]['ngay'] ?? '',
                          style: const TextStyle(
                              fontSize: 10, color: AppTheme.textMuted)),
                    );
                  }
                  return const Text('');
                },
              ),
            ),
          ),
          borderData: FlBorderData(show: false),
          lineBarsData: [
            LineChartBarData(
              spots: spots,
              isCurved: true,
              color: AppTheme.secondary,
              barWidth: 4,
              isStrokeCapRound: true,
              dotData: FlDotData(
                show: true,
                getDotPainter: (spot, percent, barData, index) =>
                    FlDotCirclePainter(
                        radius: 4,
                        color: AppTheme.secondary,
                        strokeWidth: 2,
                        strokeColor: AppTheme.background),
              ),
              belowBarData: BarAreaData(
                show: true,
                gradient: LinearGradient(
                  colors: [
                    AppTheme.secondary.withValues(alpha: 0.3),
                    AppTheme.secondary.withValues(alpha: 0.0)
                  ],
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildClassList() {
    if (_classStats.isEmpty) {
      return const Text("Không có dữ liệu lớp",
          style: TextStyle(color: AppTheme.textMuted));
    }

    return ListView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      itemCount: _classStats.length,
      itemBuilder: (context, index) {
        final c = _classStats[index];
        final total = c['tong_sv'] ?? 0;
        final present = c['so_co_mat_hom_nay'] ?? 0;
        final percent = total > 0 ? (present / total) : 0.0;

        // Màu sắc cảnh báo dựa trên tỷ lệ
        Color progressColor = AppTheme.success;
        if (percent < 0.5) {
          progressColor = AppTheme.error;
        } else if (percent < 0.8) progressColor = AppTheme.secondary;

        return NeuContainer(
          margin: const EdgeInsets.only(bottom: 12),
          padding: const EdgeInsets.all(16),
          borderRadius: 16,
          child: Column(
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(c['ten_lop'] ?? '',
                            style: const TextStyle(
                                fontWeight: FontWeight.bold,
                                color: AppTheme.textPrimary,
                                fontSize: 15)),
                        const SizedBox(height: 4),
                        Text(c['ma_lop'] ?? '',
                            style: const TextStyle(
                                fontSize: 12, color: AppTheme.textSecondary)),
                      ]),
                  Text("${(percent * 100).toStringAsFixed(0)}%",
                      style: TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                          color: progressColor)),
                ],
              ),
              const SizedBox(height: 16),
              ClipRRect(
                borderRadius: BorderRadius.circular(10),
                child: LinearProgressIndicator(
                  value: percent,
                  minHeight: 8,
                  backgroundColor: Colors.white.withValues(alpha: 0.1),
                  color: progressColor,
                ),
              ),
              const SizedBox(height: 12),
              Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
                _buildSmallStatItem(Icons.people, "Sĩ số: $total"),
                _buildSmallStatItem(Icons.check_circle, "Có mặt: $present",
                    color: AppTheme.success),
              ]),
            ],
          ),
        );
      },
    );
  }

  Widget _buildAbsentRiskList() {
    if (_absentRisk.isEmpty) {
      return NeuContainer(
        padding: const EdgeInsets.all(20),
        borderRadius: 16,
        child: const Center(
            child: Text("Hệ thống ổn định, không có cảnh báo vắng.",
                style: TextStyle(color: AppTheme.success))),
      );
    }

    return NeuContainer(
      borderRadius: 20,
      child: ListView.separated(
        shrinkWrap: true,
        physics: const NeverScrollableScrollPhysics(),
        itemCount: _absentRisk.length,
        separatorBuilder: (context, index) => Divider(
            height: 1, color: Colors.white.withValues(alpha: 0.05), indent: 70),
        itemBuilder: (context, index) {
          final s = _absentRisk[index];
          final total = s['tong_buoi_hoc'] ?? 0;
          final present = s['so_buoi_di'] ?? 0;
          final absent = total - present;

          return ListTile(
            contentPadding:
                const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
            leading: Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                  color: AppTheme.error.withValues(alpha: 0.15),
                  shape: BoxShape.circle),
              child:
                  const Icon(Icons.person_off, color: AppTheme.error, size: 20),
            ),
            title: Text(s['ho_ten'] ?? '',
                style: const TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                    color: AppTheme.textPrimary)),
            subtitle: Padding(
              padding: const EdgeInsets.only(top: 4),
              child: Text("${s['mssv']} • ${s['ma_lop']}",
                  style: const TextStyle(
                      fontSize: 12, color: AppTheme.textSecondary)),
            ),
            trailing: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text("Vắng $absent",
                    style: const TextStyle(
                        color: AppTheme.error,
                        fontWeight: FontWeight.bold,
                        fontSize: 14)),
                const SizedBox(height: 2),
                Text("Tổng $total",
                    style: const TextStyle(
                        fontSize: 10, color: AppTheme.textMuted)),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildSmallStatItem(IconData icon, String text,
      {Color color = AppTheme.textMuted}) {
    return Row(
      children: [
        Icon(icon, size: 14, color: color),
        const SizedBox(width: 4),
        Text(text,
            style: TextStyle(
                fontSize: 12, color: color, fontWeight: FontWeight.w500)),
      ],
    );
  }
}
