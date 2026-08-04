import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:image_picker/image_picker.dart';
import 'dart:io';

import '../models/leave_request_model.dart';
import '../services/leave_service.dart';
import '../theme/app_theme.dart';
import '../widgets/neu_container.dart';
import '../widgets/neu_button.dart';

class StudentLeaveScreen extends StatefulWidget {
  const StudentLeaveScreen({super.key});

  @override
  State<StudentLeaveScreen> createState() => _StudentLeaveScreenState();
}

class _StudentLeaveScreenState extends State<StudentLeaveScreen> {
  final LeaveService _leaveService = LeaveService();
  List<LeaveRequest> _requests = [];
  bool _isLoading = true;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _loadRequests();
  }

  Future<void> _loadRequests() async {
    setState(() => _isLoading = true);
    final result = await _leaveService.getMyLeaveRequests();
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

  void _showCreateForm() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => const _CreateLeaveForm(),
    ).then((_) => _loadRequests());
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      appBar: AppBar(
        title: const Text('Đơn xin phép',
            style: TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: Colors.transparent,
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadRequests,
          ),
        ],
      ),
      body: _isLoading
          ? const Center(
              child: CircularProgressIndicator(color: AppTheme.primary))
          : _errorMessage != null
              ? Center(
                  child: Text(_errorMessage!,
                      style: const TextStyle(color: AppTheme.error)))
              : _requests.isEmpty
                  ? Center(
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          const Icon(Icons.description_outlined,
                              size: 64, color: AppTheme.textMuted),
                          const SizedBox(height: 16),
                          const Text('Bạn chưa có đơn xin phép nào',
                              style: TextStyle(color: AppTheme.textSecondary)),
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
                          return _buildRequestCard(req, i);
                        },
                      ),
                    ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _showCreateForm,
        backgroundColor: AppTheme.primary,
        icon: const Icon(Icons.add, color: Colors.white),
        label: const Text('Tạo đơn',
            style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
      ).animate().scale(delay: 500.ms),
    );
  }

  Widget _buildRequestCard(LeaveRequest req, int index) {
    Color statusColor;
    String statusText;
    IconData statusIcon;

    if (req.trangThai == 1) {
      statusColor = AppTheme.success;
      statusText = 'Đã duyệt';
      statusIcon = Icons.check_circle;
    } else if (req.trangThai == 2) {
      statusColor = AppTheme.error;
      statusText = 'Từ chối';
      statusIcon = Icons.cancel;
    } else {
      statusColor = AppTheme.warning;
      statusText = 'Đang chờ';
      statusIcon = Icons.hourglass_empty;
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
              Text(
                req.tenLop ?? 'Lớp không xác định',
                style: const TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 16,
                    color: AppTheme.textPrimary),
              ),
              Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: statusColor.withValues(alpha: 0.15),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(color: statusColor.withValues(alpha: 0.5)),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(statusIcon, size: 14, color: statusColor),
                    const SizedBox(width: 4),
                    Text(statusText,
                        style: TextStyle(
                            color: statusColor,
                            fontSize: 12,
                            fontWeight: FontWeight.bold)),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            req.lyDo,
            style: const TextStyle(color: AppTheme.textSecondary, fontSize: 14),
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              const Icon(Icons.access_time,
                  size: 14, color: AppTheme.textMuted),
              const SizedBox(width: 4),
              Text(
                req.thoiGianTao ?? '',
                style: const TextStyle(color: AppTheme.textMuted, fontSize: 12),
              ),
            ],
          ),
        ],
      ),
    ).animate().fadeIn(delay: Duration(milliseconds: index * 100)).slideX();
  }
}

class _CreateLeaveForm extends StatefulWidget {
  const _CreateLeaveForm();

  @override
  State<_CreateLeaveForm> createState() => _CreateLeaveFormState();
}

class _CreateLeaveFormState extends State<_CreateLeaveForm> {
  final TextEditingController _lyDoController = TextEditingController();
  int? _selectedLopId;
  List<dynamic> _classes = [];
  bool _isLoadingClasses = true;
  XFile? _imageFile;
  bool _isSubmitting = false;

  @override
  void initState() {
    super.initState();
    _loadClasses();
  }

  Future<void> _loadClasses() async {
    final result = await LeaveService().getClasses();
    if (!mounted) return;
    if (result['success'] == true) {
      setState(() {
        _classes =
            result['data'] != null ? List<dynamic>.from(result['data']) : [];
        if (_classes.isNotEmpty) {
          _selectedLopId = int.parse(_classes[0]['id'].toString());
        }
        _isLoadingClasses = false;
      });
    } else {
      setState(() => _isLoadingClasses = false);
    }
  }

  Future<void> _pickImage() async {
    final picker = ImagePicker();
    final pickedFile =
        await picker.pickImage(source: ImageSource.gallery, imageQuality: 70);
    if (pickedFile != null) {
      setState(() => _imageFile = pickedFile);
    }
  }

  Future<void> _submit() async {
    if (_selectedLopId == null || _lyDoController.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Vui lòng chọn lớp và nhập Lý do')));
      return;
    }

    setState(() => _isSubmitting = true);

    String? base64Image;
    try {
      if (_imageFile != null) {
        final bytes = await _imageFile!.readAsBytes();
        base64Image = base64Encode(bytes);
      }
    } catch (e) {
      if (!mounted) return;
      setState(() => _isSubmitting = false);
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text('Lỗi đọc ảnh: $e'), backgroundColor: AppTheme.error));
      return;
    }

    final result = await LeaveService().submitLeaveRequest(
      _selectedLopId!,
      _lyDoController.text,
      base64Image,
    );

    if (!mounted) return;
    setState(() => _isSubmitting = false);

    if (result['success'] == true) {
      Navigator.pop(context, true);
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text('Gửi đơn thành công'),
          backgroundColor: AppTheme.success));
    } else {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text(result['message'] ?? 'Lỗi gửi đơn'),
          backgroundColor: AppTheme.error));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.only(
        bottom: MediaQuery.of(context).viewInsets.bottom,
        left: 20,
        right: 20,
        top: 20,
      ),
      decoration: const BoxDecoration(
        color: AppTheme.surface,
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Center(
              child: Container(
                  width: 40,
                  height: 5,
                  decoration: BoxDecoration(
                      color: Colors.grey[600],
                      borderRadius: BorderRadius.circular(10))),
            ),
            const SizedBox(height: 20),
            const Text('Tạo đơn xin phép',
                style: TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                    color: AppTheme.textPrimary)),
            const SizedBox(height: 20),

            // Lớp ID Input (Dropdown)
            NeuContainer(
              isPressed: true,
              child: _isLoadingClasses
                  ? const Padding(
                      padding: EdgeInsets.all(16.0),
                      child: Center(
                          child: CircularProgressIndicator(
                              color: AppTheme.primary)),
                    )
                  : DropdownButtonFormField<int>(
                      value: _selectedLopId,
                      items: _classes.map((c) {
                        return DropdownMenuItem<int>(
                          value: c['id'],
                          child: Text('${c['ten_lop']} (${c['ma_lop']})',
                              style:
                                  const TextStyle(color: AppTheme.textPrimary)),
                        );
                      }).toList(),
                      onChanged: (val) {
                        setState(() => _selectedLopId = val);
                      },
                      dropdownColor: AppTheme.surface,
                      style: const TextStyle(color: AppTheme.textPrimary),
                      decoration: const InputDecoration(
                        labelText: 'Lớp học',
                        labelStyle: TextStyle(color: AppTheme.textSecondary),
                        border: InputBorder.none,
                        prefixIcon: Icon(Icons.class_, color: AppTheme.primary),
                        contentPadding: EdgeInsets.all(16),
                      ),
                    ),
            ),
            const SizedBox(height: 16),

            // Lý do Input
            NeuContainer(
              isPressed: true,
              child: TextField(
                controller: _lyDoController,
                maxLines: 3,
                style: const TextStyle(color: AppTheme.textPrimary),
                decoration: const InputDecoration(
                  labelText: 'Lý do vắng mặt',
                  border: InputBorder.none,
                  prefixIcon: Padding(
                    padding: EdgeInsets.only(bottom: 40),
                    child: Icon(Icons.edit_note, color: AppTheme.primary),
                  ),
                  contentPadding: EdgeInsets.all(16),
                ),
              ),
            ),
            const SizedBox(height: 16),

            // Image Picker
            GestureDetector(
              onTap: _pickImage,
              child: NeuContainer(
                padding: const EdgeInsets.all(16),
                child: Row(
                  children: [
                    const Icon(Icons.image, color: AppTheme.secondary),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        _imageFile != null
                            ? 'Đã chọn ảnh minh chứng'
                            : 'Đính kèm ảnh minh chứng (Giấy khám bệnh, etc.)',
                        style: TextStyle(
                            color: _imageFile != null
                                ? AppTheme.success
                                : AppTheme.textSecondary),
                      ),
                    ),
                    if (_imageFile != null)
                      const Icon(Icons.check_circle, color: AppTheme.success),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 24),
            SizedBox(
              width: double.infinity,
              child: NeuButton(
                isPrimary: true,
                onPressed: _isSubmitting ? null : _submit,
                child: Center(
                  child: _isSubmitting
                      ? const SizedBox(
                          width: 24,
                          height: 24,
                          child: CircularProgressIndicator(
                              color: Colors.white, strokeWidth: 2))
                      : const Text('GỬI ĐƠN',
                          style: TextStyle(fontWeight: FontWeight.bold)),
                ),
              ),
            ),
            const SizedBox(height: 32),
          ],
        ),
      ),
    );
  }
}
