import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../services/api_service.dart';
import '../theme/app_theme.dart';

class ScheduleScreen extends StatefulWidget {
  const ScheduleScreen({super.key});

  @override
  _ScheduleScreenState createState() => _ScheduleScreenState();
}

class _ScheduleScreenState extends State<ScheduleScreen> {
  final ApiService _apiService = ApiService();
  List<dynamic> _schedules = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _fetchSchedule();
  }

  Future<void> _fetchSchedule() async {
    try {
      final res = await _apiService.getSchedule();
      if (mounted) {
        setState(() {
          _schedules = res['data'] ?? [];
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isLoading = false);
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Lỗi tải lịch: $e")));
      }
    }
  }

  String _getThuString(int thu) {
    if (thu == 8) return "Chủ Nhật";
    return "Thứ $thu";
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: AppBar(
        title: const Text("Lịch học MTU"),
        backgroundColor: Colors.transparent,
        foregroundColor: AppTheme.textPrimary,
        elevation: 0,
      ),
      body: Stack(
        children: [
          // Ambient Glow
          Positioned(
            top: -100,
            right: -50,
            child: Container(
              width: 300,
              height: 300,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: AppTheme.secondary.withOpacity(0.15),
                backgroundBlendMode: BlendMode.screen,
              ),
            ),
          ),
          
          _isLoading
              ? const Center(child: CircularProgressIndicator(color: AppTheme.secondary))
              : _schedules.isEmpty
                  ? _buildEmptyState()
                  : ListView.builder(
                      padding: const EdgeInsets.all(20),
                      itemCount: _schedules.length,
                      itemBuilder: (context, index) {
                        final item = _schedules[index];
                        return _buildScheduleCard(item, index);
                      },
                    ),
        ],
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: const Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.calendar_today_outlined, size: 80, color: AppTheme.textMuted),
          SizedBox(height: 16),
          Text("Chưa có dữ liệu lịch học", style: TextStyle(color: AppTheme.textSecondary, fontSize: 16)),
        ],
      ).animate().fadeIn(duration: 400.ms).scale(begin: const Offset(0.8, 0.8)),
    );
  }

  Widget _buildScheduleCard(dynamic item, int index) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      decoration: AppTheme.glassDecoration(borderRadius: 16, opacity: 0.05),
      child: IntrinsicHeight(
        child: Row(
          children: [
            // Cột hiển thị Thứ
            Container(
              width: 80,
              decoration: const BoxDecoration(
                color: AppTheme.surfaceLight,
                borderRadius: BorderRadius.only(topLeft: Radius.circular(16), bottomLeft: Radius.circular(16)),
              ),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(
                    _getThuString(item['thu']), 
                    style: const TextStyle(color: AppTheme.secondary, fontWeight: FontWeight.bold, fontSize: 16),
                  ),
                ],
              ),
            ),
            // Thông tin môn học
            Expanded(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      item['mon_hoc'] ?? 'Môn học', 
                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18, color: AppTheme.textPrimary),
                    ),
                    const SizedBox(height: 12),
                    Row(
                      children: [
                        const Icon(Icons.access_time, size: 16, color: AppTheme.accent),
                        const SizedBox(width: 6),
                        Text(
                          "Tiết ${item['tiet_bat_dau']} - ${item['tiet_bat_dau'] + item['so_tiet'] - 1}", 
                          style: const TextStyle(fontSize: 14, color: AppTheme.textSecondary),
                        ),
                        const Spacer(),
                        const Icon(Icons.room, size: 16, color: AppTheme.primary),
                        const SizedBox(width: 6),
                        Text(
                          "${item['phong_hoc']}", 
                          style: const TextStyle(fontSize: 14, color: AppTheme.textSecondary),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        const Icon(Icons.person, size: 16, color: AppTheme.textMuted),
                        const SizedBox(width: 6),
                        Text(
                          "GV: ${item['giang_vien']}", 
                          style: const TextStyle(fontSize: 13, color: AppTheme.textSecondary, fontStyle: FontStyle.italic),
                        ),
                      ],
                    )
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    ).animate().fadeIn(delay: Duration(milliseconds: 100 * index)).slideX(begin: 0.1, end: 0);
  }
}
