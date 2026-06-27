import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../models/leave_request_model.dart';
import '../services/leave_service.dart';
import '../services/api_service.dart';
import '../theme/app_theme.dart';
import '../widgets/neu_container.dart';
import '../widgets/neu_button.dart';

class AdminLeaveScreen extends StatefulWidget {
  const AdminLeaveScreen({super.key});

  @override
  State<AdminLeaveScreen> createState() => _AdminLeaveScreenState();
}

class _AdminLeaveScreenState extends State<AdminLeaveScreen> {
  final LeaveService _leaveService = LeaveService();
  List<LeaveRequest> _requests = [];
  bool _isLoading = true;
  String? _errorMessage;
  int _selectedFilter = -1; // -1: All, 0: Pending, 1: Approved, 2: Rejected

  @override
  void initState() {
    super.initState();
    _loadRequests();
  }

  Future<void> _loadRequests() async {
    setState(() => _isLoading = true);
    final result = await _leaveService.getAdminLeaveRequests(
      status: _selectedFilter == -1 ? null : _selectedFilter,
    );
    if (!mounted) return;
    if (result['success'] == true) {
      setState(() {
        _requests = result['data'];
        _isLoading = false;
        _errorMessage = null;
      });
    } else {
      setState(() {
        _errorMessage = result['message'];
        _isLoading = false;
      });
    }
  }

  Future<void> _updateStatus(int requestId, int newStatus) async {
    final result = newStatus == 1 
        ? await _leaveService.approveLeaveRequest(requestId)
        : await _leaveService.rejectLeaveRequest(requestId);
        
    if (!mounted) return;
    if (result['success'] == true) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content: Text(result['message']),
        backgroundColor: newStatus == 1 ? AppTheme.success : AppTheme.error,
      ));
      _loadRequests();
    } else {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content: Text(result['message'] ?? 'Lỗi cập nhật'),
        backgroundColor: AppTheme.error,
      ));
    }
  }

  void _showImageDialog(String imageUrl) {
    showDialog(
      context: context,
      builder: (context) => Dialog(
        backgroundColor: Colors.transparent,
        child: ClipRRect(
          borderRadius: BorderRadius.circular(16),
          child: Image.network(
            '${ApiService.baseUrl}$imageUrl',
            fit: BoxFit.contain,
            errorBuilder: (c, e, s) => Container(
              color: AppTheme.surface,
              padding: const EdgeInsets.all(40),
              child: const Icon(Icons.broken_image, size: 60, color: AppTheme.textMuted),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildFilterChip(String label, int value) {
    final isSelected = _selectedFilter == value;
    return Padding(
      padding: const EdgeInsets.only(right: 8),
      child: GestureDetector(
        onTap: () {
          setState(() => _selectedFilter = value);
          _loadRequests();
        },
        child: NeuContainer(
          isPressed: isSelected,
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          borderRadius: 20,
          child: Text(
            label,
            style: TextStyle(
              color: isSelected ? AppTheme.primary : AppTheme.textSecondary,
              fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
            ),
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      appBar: AppBar(
        title: const Text('Quản lý đơn từ', style: TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: Colors.transparent,
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadRequests,
          ),
        ],
      ),
      body: Column(
        children: [
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: Row(
              children: [
                _buildFilterChip('Tất cả', -1),
                _buildFilterChip('Đang chờ', 0),
                _buildFilterChip('Đã duyệt', 1),
                _buildFilterChip('Từ chối', 2),
              ],
            ),
          ),
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator(color: AppTheme.primary))
                : _errorMessage != null
                    ? Center(child: Text(_errorMessage!, style: const TextStyle(color: AppTheme.error)))
                    : _requests.isEmpty
                        ? Center(
                            child: Column(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                const Icon(Icons.folder_open, size: 64, color: AppTheme.textMuted),
                                const SizedBox(height: 16),
                                const Text('Không có đơn xin phép nào', style: TextStyle(color: AppTheme.textSecondary)),
                              ],
                            ).animate().fadeIn(),
                          )
                        : RefreshIndicator(
                            onRefresh: _loadRequests,
                            child: ListView.builder(
                              padding: const EdgeInsets.all(16),
                              itemCount: _requests.length,
                              itemBuilder: (ctx, i) {
                                final req = _requests[i];
                                return _buildAdminRequestCard(req, i);
                              },
                            ),
                          ),
          ),
        ],
      ),
    );
  }

  Widget _buildAdminRequestCard(LeaveRequest req, int index) {
    Color statusColor;
    String statusText;
    
    if (req.trangThai == 1) {
      statusColor = AppTheme.success;
      statusText = 'Đã duyệt';
    } else if (req.trangThai == 2) {
      statusColor = AppTheme.error;
      statusText = 'Từ chối';
    } else {
      statusColor = AppTheme.warning;
      statusText = 'Đang chờ';
    }

    return NeuContainer(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(16),
      borderRadius: 16,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      req.hoTen ?? 'Không rõ',
                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: AppTheme.textPrimary),
                    ),
                    Text(
                      '${req.mssv ?? ''} - ${req.tenLop ?? ''}',
                      style: const TextStyle(color: AppTheme.textMuted, fontSize: 13),
                    ),
                  ],
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: statusColor.withValues(alpha: 0.15),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(color: statusColor.withValues(alpha: 0.5)),
                ),
                child: Text(statusText, style: TextStyle(color: statusColor, fontSize: 12, fontWeight: FontWeight.bold)),
              ),
            ],
          ),
          const SizedBox(height: 12),
          const Text('Lý do:', style: TextStyle(color: AppTheme.textMuted, fontSize: 12)),
          Text(
            req.lyDo,
            style: const TextStyle(color: AppTheme.textSecondary, fontSize: 14),
          ),
          const SizedBox(height: 12),
          
          if (req.minhChungUrl != null && req.minhChungUrl!.isNotEmpty)
            GestureDetector(
              onTap: () => _showImageDialog(req.minhChungUrl!),
              child: Container(
                margin: const EdgeInsets.only(bottom: 12),
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: Colors.white.withValues(alpha: 0.05),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.image, color: AppTheme.secondary, size: 20),
                    const SizedBox(width: 8),
                    const Expanded(child: Text('Xem ảnh minh chứng', style: TextStyle(color: AppTheme.secondary, fontSize: 13))),
                    Icon(Icons.zoom_in, color: AppTheme.secondary.withValues(alpha: 0.5), size: 18),
                  ],
                ),
              ),
            ),
          
          Row(
            children: [
              const Icon(Icons.access_time, size: 14, color: AppTheme.textMuted),
              const SizedBox(width: 4),
              Text(
                req.thoiGianTao ?? '',
                style: const TextStyle(color: AppTheme.textMuted, fontSize: 12),
              ),
            ],
          ),
          
          if (req.trangThai == 0) ...[
            const SizedBox(height: 16),
            const Divider(color: Colors.white12),
            const SizedBox(height: 8),
            Row(
              children: [
                Expanded(
                  child: NeuButton(
                    onPressed: () => _updateStatus(req.id, 2),
                    child: const Text('TỪ CHỐI', style: TextStyle(color: AppTheme.error, fontWeight: FontWeight.bold)),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: NeuButton(
                    isPrimary: true,
                    onPressed: () => _updateStatus(req.id, 1),
                    child: const Text('DUYỆT ĐƠN', style: TextStyle(fontWeight: FontWeight.bold, color: Colors.white)),
                  ),
                ),
              ],
            ),
          ]
        ],
      ),
    ).animate().fadeIn(delay: Duration(milliseconds: index * 100)).slideY(begin: 0.1, end: 0);
  }
}
