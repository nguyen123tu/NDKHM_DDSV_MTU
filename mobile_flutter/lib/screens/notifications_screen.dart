import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../services/api_service.dart';
import '../theme/app_theme.dart';

class NotificationsScreen extends StatefulWidget {
  const NotificationsScreen({super.key});

  @override
  State<NotificationsScreen> createState() => _NotificationsScreenState();
}

class _NotificationsScreenState extends State<NotificationsScreen> {
  final ApiService _api = ApiService();
  bool _isLoading = true;
  List<dynamic> _notifications = [];

  @override
  void initState() {
    super.initState();
    _loadNotifications();
  }

  Future<void> _loadNotifications() async {
    setState(() => _isLoading = true);
    try {
      final result = await _api.getNotifications();
      if (mounted) {
        setState(() {
          _notifications = result['data'] ?? [];
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  Future<void> _markRead(int id) async {
    await _api.markNotificationRead(id);
    _loadNotifications();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: AppBar(
        title: const Text('Thông Báo', style: TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: Colors.transparent,
        foregroundColor: AppTheme.textPrimary,
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh, color: AppTheme.textSecondary), 
            onPressed: _loadNotifications
          ),
        ],
      ),
      body: Stack(
        children: [
          // Ambient Glow
          Positioned(
            top: -100,
            left: -50,
            child: Container(
              width: 300,
              height: 300,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: AppTheme.primary.withOpacity(0.15),
                backgroundBlendMode: BlendMode.screen,
              ),
            ),
          ),

          _isLoading
              ? const Center(child: CircularProgressIndicator(color: AppTheme.primary))
              : RefreshIndicator(
                  onRefresh: _loadNotifications,
                  color: AppTheme.primary,
                  backgroundColor: AppTheme.surfaceLight,
                  child: _notifications.isEmpty
                      ? _buildEmptyState()
                      : ListView.builder(
                          padding: const EdgeInsets.all(20),
                          itemCount: _notifications.length,
                          itemBuilder: (context, index) {
                            final n = _notifications[index];
                            final isRead = n['da_doc'] == 1;

                            return _buildNotificationCard(n, isRead, index);
                          },
                        ),
                ),
        ],
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.notifications_none, size: 80, color: AppTheme.textMuted),
          const SizedBox(height: 16),
          Text('Bạn không có thông báo nào', style: TextStyle(color: AppTheme.textSecondary, fontSize: 16)),
        ],
      ).animate().fadeIn(duration: 400.ms).scale(begin: const Offset(0.8, 0.8)),
    );
  }

  Widget _buildNotificationCard(dynamic n, bool isRead, int index) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      decoration: AppTheme.glassDecoration(
        borderRadius: 16, 
        opacity: isRead ? 0.03 : 0.08,
      ).copyWith(
        border: Border.all(
          color: isRead ? Colors.white10 : AppTheme.primary.withOpacity(0.5),
          width: 1,
        ),
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          borderRadius: BorderRadius.circular(16),
          onTap: isRead ? null : () => _markRead(n['id']),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Icon
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: isRead ? AppTheme.surfaceLight : AppTheme.primary.withOpacity(0.15),
                    shape: BoxShape.circle,
                  ),
                  child: Icon(
                    isRead ? Icons.notifications_outlined : Icons.notifications_active,
                    color: isRead ? AppTheme.textMuted : AppTheme.primary,
                    size: 24,
                  ),
                ),
                const SizedBox(width: 16),
                // Content
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        n['tieu_de'] ?? 'Thông báo',
                        style: TextStyle(
                          fontWeight: isRead ? FontWeight.normal : FontWeight.bold,
                          fontSize: 16,
                          color: isRead ? AppTheme.textSecondary : AppTheme.textPrimary,
                        ),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        n['noi_dung'] ?? '', 
                        style: TextStyle(
                          fontSize: 14, 
                          color: isRead ? AppTheme.textMuted : AppTheme.textSecondary,
                          height: 1.4,
                        ),
                      ),
                      const SizedBox(height: 12),
                      Text(
                        n['created_at'] ?? '', 
                        style: TextStyle(fontSize: 12, color: AppTheme.textMuted),
                      ),
                    ],
                  ),
                ),
                // Unread Dot
                if (!isRead)
                  Container(
                    width: 10,
                    height: 10,
                    margin: const EdgeInsets.only(top: 8),
                    decoration: BoxDecoration(
                      color: AppTheme.secondary,
                      shape: BoxShape.circle,
                      boxShadow: [
                        BoxShadow(color: AppTheme.secondary.withOpacity(0.5), blurRadius: 8, spreadRadius: 2)
                      ],
                    ),
                  ).animate(onPlay: (controller) => controller.repeat(reverse: true))
                   .fade(begin: 0.5, end: 1.0)
                   .scale(begin: const Offset(0.8, 0.8), end: const Offset(1.2, 1.2)),
              ],
            ),
          ),
        ),
      ),
    ).animate().fadeIn(delay: Duration(milliseconds: 100 * index)).slideY(begin: 0.2, end: 0);
  }
}
