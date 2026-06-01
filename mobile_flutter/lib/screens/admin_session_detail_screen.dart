import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../services/api_service.dart';
import '../services/export_service.dart';
import '../theme/app_theme.dart';

class AdminSessionDetailScreen extends StatefulWidget {
  final int sessionId;
  final String tenLop;

  const AdminSessionDetailScreen({
    super.key,
    required this.sessionId,
    required this.tenLop,
  });

  @override
  State<AdminSessionDetailScreen> createState() => _AdminSessionDetailScreenState();
}

class _AdminSessionDetailScreenState extends State<AdminSessionDetailScreen> {
  final ApiService _api = ApiService();
  bool _isLoading = true;
  Map<String, dynamic>? _sessionData;
  List<dynamic> _students = [];
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadDetails();
  }

  Future<void> _loadDetails() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });
    try {
      final result = await _api.getSessionDetails(widget.sessionId);
      if (mounted) {
        if (result['success'] == true) {
          setState(() {
            _sessionData = result['data']['session'];
            _students = result['data']['students'];
            _isLoading = false;
          });
        } else {
          setState(() {
            _error = result['message'];
            _isLoading = false;
          });
        }
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = 'Lỗi kết nối: $e';
          _isLoading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: AppBar(
        title: Text('Chi tiết: ${widget.tenLop}', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
        backgroundColor: Colors.transparent,
        foregroundColor: AppTheme.textPrimary,
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.download, color: AppTheme.primary),
            onPressed: () {
              if (_students.isNotEmpty) {
                ExportService.exportSessionToExcel(_students, widget.tenLop);
              }
            },
          ),
          IconButton(
            icon: const Icon(Icons.refresh, color: AppTheme.secondary),
            onPressed: _loadDetails,
          ),
        ],
      ),
      body: Stack(
        children: [
          // Ambient Glow Background
          Positioned(
            top: -100,
            left: -100,
            child: ImageFiltered(
              imageFilter: ImageFilter.blur(sigmaX: 80, sigmaY: 80),
              child: Container(
                width: 300,
                height: 300,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: AppTheme.primary.withOpacity(0.15),
                ),
              ),
            ),
          ),
          Positioned(
            bottom: -50,
            right: -50,
            child: ImageFiltered(
              imageFilter: ImageFilter.blur(sigmaX: 80, sigmaY: 80),
              child: Container(
                width: 250,
                height: 250,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: AppTheme.secondary.withOpacity(0.1),
                ),
              ),
            ),
          ),

          _isLoading
              ? const Center(child: CircularProgressIndicator(color: AppTheme.primary))
              : _error != null
                  ? Center(child: Text(_error!, style: const TextStyle(color: Colors.redAccent)))
                  : _buildContent(),
        ],
      ),
    );
  }

  Widget _buildContent() {
    int present = _students.where((s) => s['trang_thai'] == 'Co mat').length;
    int absent = _students.length - present;

    return Column(
      children: [
        // Header Stats
        Container(
          margin: const EdgeInsets.all(16),
          padding: const EdgeInsets.symmetric(vertical: 20),
          decoration: AppTheme.glassDecoration(borderRadius: 20, opacity: 0.05),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              _buildStatInfo('Tổng SV', _students.length.toString(), AppTheme.primary, Icons.groups),
              Container(width: 1, height: 40, color: Colors.white10),
              _buildStatInfo('Có mặt', present.toString(), Colors.greenAccent, Icons.how_to_reg),
              Container(width: 1, height: 40, color: Colors.white10),
              _buildStatInfo('Vắng', absent.toString(), Colors.redAccent, Icons.person_off),
            ],
          ),
        ).animate().fadeIn(duration: 400.ms).slideY(begin: -0.1, end: 0),

        // Student list
        Expanded(
          child: ListView.builder(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            itemCount: _students.length,
            itemBuilder: (context, index) {
              final student = _students[index];
              bool isPresent = student['trang_thai'] == 'Co mat';
              
              return Container(
                margin: const EdgeInsets.only(bottom: 12),
                decoration: AppTheme.glassDecoration(
                  borderRadius: 16, 
                  opacity: isPresent ? 0.05 : 0.02,
                ).copyWith(
                  border: Border.all(
                    color: isPresent ? Colors.greenAccent.withOpacity(0.2) : Colors.redAccent.withOpacity(0.1),
                  ),
                ),
                child: ListTile(
                  contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                  leading: Container(
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: isPresent ? Colors.greenAccent.withOpacity(0.1) : Colors.redAccent.withOpacity(0.1),
                      shape: BoxShape.circle,
                    ),
                    child: Icon(
                      isPresent ? Icons.check_circle_outline : Icons.cancel_outlined,
                      color: isPresent ? Colors.greenAccent : Colors.redAccent,
                      size: 24,
                    ),
                  ),
                  title: Text(
                    student['ho_ten'] ?? 'Chưa cập nhật', 
                    style: const TextStyle(fontWeight: FontWeight.bold, color: AppTheme.textPrimary, fontSize: 16),
                  ),
                  subtitle: Padding(
                    padding: const EdgeInsets.only(top: 4),
                    child: Text(
                      student['mssv'] ?? '', 
                      style: const TextStyle(color: AppTheme.textMuted, fontSize: 13),
                    ),
                  ),
                  trailing: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(
                          color: isPresent ? Colors.greenAccent.withOpacity(0.1) : Colors.redAccent.withOpacity(0.1),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Text(
                          isPresent ? 'CÓ MẶT' : 'VẮNG',
                          style: TextStyle(
                            color: isPresent ? Colors.greenAccent : Colors.redAccent,
                            fontWeight: FontWeight.bold,
                            fontSize: 11,
                          ),
                        ),
                      ),
                      const SizedBox(height: 6),
                      if (student['thoi_gian'] != null)
                        Text(
                          student['thoi_gian'].toString(),
                          style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary, fontFamily: 'monospace'),
                        ),
                    ],
                  ),
                ),
              ).animate().fadeIn(delay: Duration(milliseconds: 50 * index)).slideX(begin: 0.1, end: 0);
            },
          ),
        ),
      ],
    );
  }

  Widget _buildStatInfo(String label, String value, Color color, IconData icon) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, color: color, size: 24),
        const SizedBox(height: 8),
        Text(value, style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: color)),
        const SizedBox(height: 4),
        Text(label, style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary, fontWeight: FontWeight.w500)),
      ],
    );
  }
}
