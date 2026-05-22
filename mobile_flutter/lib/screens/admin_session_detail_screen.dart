import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../services/export_service.dart';

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
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        title: Text('Chi tiết phiên: ${widget.tenLop}', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
        backgroundColor: const Color(0xFF1E293B),
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.download),
            onPressed: () {
              if (_students.isNotEmpty) {
                ExportService.exportSessionToExcel(_students, widget.tenLop);
              }
            },
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadDetails,
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: Color(0xFF1E293B)))
          : _error != null
              ? Center(child: Text(_error!, style: const TextStyle(color: Colors.red)))
              : _buildContent(),
    );
  }

  Widget _buildContent() {
    int present = _students.where((s) => s['trang_thai'] == 'Co mat').length;
    int absent = _students.length - present;

    return Column(
      children: [
        // Header info
        Container(
          padding: const EdgeInsets.all(16),
          color: Colors.white,
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _buildStatInfo('Tổng số SV', _students.length.toString(), Colors.blue),
              _buildStatInfo('Có mặt', present.toString(), Colors.green),
              _buildStatInfo('Vắng', absent.toString(), Colors.red),
            ],
          ),
        ),
        const SizedBox(height: 8),
        // Student list
        Expanded(
          child: ListView.builder(
            itemCount: _students.length,
            itemBuilder: (context, index) {
              final student = _students[index];
              bool isPresent = student['trang_thai'] == 'Co mat';
              
              return Card(
                margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                child: ListTile(
                  leading: CircleAvatar(
                    backgroundColor: isPresent ? Colors.green.withOpacity(0.2) : Colors.red.withOpacity(0.2),
                    child: Icon(
                      isPresent ? Icons.check : Icons.close,
                      color: isPresent ? Colors.green : Colors.red,
                    ),
                  ),
                  title: Text(student['ho_ten'] ?? 'Chưa cập nhật', style: const TextStyle(fontWeight: FontWeight.bold)),
                  subtitle: Text(student['mssv'] ?? ''),
                  trailing: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      Text(
                        isPresent ? 'Có mặt' : 'Vắng',
                        style: TextStyle(
                          color: isPresent ? Colors.green : Colors.red,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      if (student['thoi_gian'] != null)
                        Text(student['thoi_gian'], style: const TextStyle(fontSize: 12, color: Colors.grey)),
                    ],
                  ),
                ),
              );
            },
          ),
        ),
      ],
    );
  }

  Widget _buildStatInfo(String label, String value, Color color) {
    return Column(
      children: [
        Text(value, style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: color)),
        const SizedBox(height: 4),
        Text(label, style: const TextStyle(fontSize: 12, color: Colors.grey)),
      ],
    );
  }
}
