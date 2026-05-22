import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import '../services/api_service.dart';

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

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        title: const Text('Thống Kê Hệ Thống', style: TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: const Color(0xFF1E293B),
        foregroundColor: Colors.white,
        elevation: 0,
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _loadAllStats),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: Color(0xFF1E293B)))
          : SingleChildScrollView(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _buildSectionTitle("Xu hướng điểm danh (7 ngày)"),
                  _buildTrendChart(),
                  const SizedBox(height: 28),
                  
                  _buildSectionTitle("Tỉ lệ đi học theo lớp"),
                  _buildClassList(),
                  const SizedBox(height: 28),
                  
                  _buildSectionTitle("Sinh viên vắng nhiều (Cảnh báo)"),
                  _buildAbsentRiskList(),
                ],
              ),
            ),
    );
  }

  Widget _buildSectionTitle(String title) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Text(title, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Color(0xFF1E293B))),
    );
  }

  Widget _buildTrendChart() {
    if (_dailyTrend.isEmpty) {
      return const Card(child: Padding(padding: EdgeInsets.all(32), child: Center(child: Text("Không có dữ liệu xu hướng"))));
    }

    return Container(
      height: 220,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 10)],
      ),
      child: LineChart(
        LineChartData(
          gridData: const FlGridData(show: false),
          titlesData: FlTitlesData(
            leftTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
            topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
            rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
            bottomTitles: AxisTitles(
              sideTitles: SideTitles(
                showTitles: true,
                getTitlesWidget: (value, meta) {
                  int index = value.toInt();
                  if (index >= 0 && index < _dailyTrend.length) {
                    return Padding(
                      padding: const EdgeInsets.only(top: 8),
                      child: Text(_dailyTrend[index]['ngay'] ?? '', style: const TextStyle(fontSize: 10, color: Colors.grey)),
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
              spots: _dailyTrend.asMap().entries.map((e) => FlSpot(e.key.toDouble(), (e.value['so_luong'] as int).toDouble())).toList(),
              isCurved: true,
              color: const Color(0xFF2E96EB),
              barWidth: 4,
              isStrokeCapRound: true,
              dotData: const FlDotData(show: true),
              belowBarData: BarAreaData(show: true, color: const Color(0xFF2E96EB).withOpacity(0.1)),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildClassList() {
    if (_classStats.isEmpty) return const Text("Không có dữ liệu lớp");

    return ListView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      itemCount: _classStats.length,
      itemBuilder: (context, index) {
        final c = _classStats[index];
        final total = c['tong_sv'] ?? 0;
        final present = c['so_co_mat_hom_nay'] ?? 0;
        final percent = total > 0 ? (present / total) : 0.0;

        return Container(
          margin: const EdgeInsets.only(bottom: 12),
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(16)),
          child: Column(
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Text(c['ten_lop'] ?? '', style: const TextStyle(fontWeight: FontWeight.bold, color: Color(0xFF1E293B))),
                    Text(c['ma_lop'] ?? '', style: const TextStyle(fontSize: 12, color: Colors.grey)),
                  ]),
                  Text("${(percent * 100).toStringAsFixed(0)}%", style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Color(0xFF10B981))),
                ],
              ),
              const SizedBox(height: 12),
              ClipRRect(
                borderRadius: BorderRadius.circular(10),
                child: LinearProgressIndicator(
                  value: percent,
                  minHeight: 8,
                  backgroundColor: Colors.grey[200],
                  color: const Color(0xFF10B981),
                ),
              ),
              const SizedBox(height: 8),
              Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
                Text("Sĩ số: $total", style: const TextStyle(fontSize: 11, color: Colors.grey)),
                Text("Hiện diện hôm nay: $present", style: const TextStyle(fontSize: 11, color: Colors.grey)),
              ]),
            ],
          ),
        );
      },
    );
  }

  Widget _buildAbsentRiskList() {
    if (_absentRisk.isEmpty) return const Text("Không có sinh viên cảnh báo");

    return Container(
      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(20)),
      child: ListView.separated(
        shrinkWrap: true,
        physics: const NeverScrollableScrollPhysics(),
        itemCount: _absentRisk.length,
        separatorBuilder: (context, index) => const Divider(height: 1),
        itemBuilder: (context, index) {
          final s = _absentRisk[index];
          final total = s['tong_buoi_hoc'] ?? 0;
          final present = s['so_buoi_di'] ?? 0;
          final absent = total - present;

          return ListTile(
            leading: CircleAvatar(
              backgroundColor: Colors.red[50],
              child: const Icon(Icons.person_off, color: Colors.redAccent, size: 20),
            ),
            title: Text(s['ho_ten'] ?? '', style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600)),
            subtitle: Text("${s['mssv']} • ${s['ma_lop']}", style: const TextStyle(fontSize: 12)),
            trailing: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text("Vắng: $absent buổi", style: const TextStyle(color: Colors.redAccent, fontWeight: FontWeight.bold, fontSize: 13)),
                Text("Trên tổng $total", style: const TextStyle(fontSize: 10, color: Colors.grey)),
              ],
            ),
          );
        },
      ),
    );
  }
}
