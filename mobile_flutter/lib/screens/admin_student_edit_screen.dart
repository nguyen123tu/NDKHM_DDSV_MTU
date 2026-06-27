import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../theme/app_theme.dart';
import '../widgets/neu_container.dart';

class AdminStudentEditScreen extends StatefulWidget {
  final Map<String, dynamic> student;
  const AdminStudentEditScreen({super.key, required this.student});

  @override
  State<AdminStudentEditScreen> createState() => _AdminStudentEditScreenState();
}

class _AdminStudentEditScreenState extends State<AdminStudentEditScreen> {
  final ApiService _api = ApiService();
  final _formKey = GlobalKey<FormState>();

  late TextEditingController _nameCtrl;
  late TextEditingController _mssvCtrl;
  late TextEditingController _classCtrl;
  late TextEditingController _emailCtrl;
  late TextEditingController _phoneCtrl;

  bool _isSaving = false;

  @override
  void initState() {
    super.initState();
    _nameCtrl = TextEditingController(text: widget.student['ho_ten']);
    _mssvCtrl = TextEditingController(text: widget.student['mssv']);
    _classCtrl = TextEditingController(text: widget.student['ma_lop']);
    _emailCtrl = TextEditingController(text: widget.student['email']);
    _phoneCtrl = TextEditingController(text: widget.student['sdt']);
  }

  @override
  void dispose() {
    _nameCtrl.dispose();
    _mssvCtrl.dispose();
    _classCtrl.dispose();
    _emailCtrl.dispose();
    _phoneCtrl.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isSaving = true);
    final data = {
      'ho_ten': _nameCtrl.text,
      'mssv': _mssvCtrl.text,
      'ma_lop': _classCtrl.text,
      'email': _emailCtrl.text,
      'sdt': _phoneCtrl.text,
    };

    final res = await _api.updateStudent(widget.student['id'], data);
    setState(() => _isSaving = false);

    if (res['success'] == true && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text('Đã cập nhật thông tin'),
          backgroundColor: AppTheme.success));
      Navigator.pop(context, true); // Return true to trigger refresh
    } else {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content: Text(res['message'] ?? 'Lỗi cập nhật'),
            backgroundColor: AppTheme.error));
      }
    }
  }

  void _confirmDelete() {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppTheme.surface,
        title: const Text('Xóa sinh viên',
            style:
                TextStyle(color: AppTheme.error, fontWeight: FontWeight.bold)),
        content: Text(
            'Bạn có chắc muốn xóa sinh viên ${_nameCtrl.text}? Hành động này không thể hoàn tác.',
            style: const TextStyle(color: AppTheme.textPrimary)),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: const Text('Hủy',
                  style: TextStyle(color: AppTheme.textMuted))),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: AppTheme.error),
            onPressed: () async {
              Navigator.pop(ctx);
              setState(() => _isSaving = true);
              final res = await _api.deleteStudent(widget.student['id']);
              setState(() => _isSaving = false);
              if (res['success'] == true && mounted) {
                ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
                    content: Text('Đã xóa sinh viên'),
                    backgroundColor: AppTheme.success));
                Navigator.pop(context, true);
              } else {
                if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(SnackBar(
                      content: Text(res['message'] ?? 'Lỗi xóa'),
                      backgroundColor: AppTheme.error));
                }
              }
            },
            child: const Text('Xóa', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );
  }

  void _confirmResetFace() {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppTheme.surface,
        title: const Text('Reset Face ID',
            style: TextStyle(
                color: AppTheme.warning, fontWeight: FontWeight.bold)),
        content: Text(
            'Xóa toàn bộ dữ liệu khuôn mặt của sinh viên ${_nameCtrl.text}? Sinh viên sẽ phải đăng ký lại.',
            style: const TextStyle(color: AppTheme.textPrimary)),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: const Text('Hủy',
                  style: TextStyle(color: AppTheme.textMuted))),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: AppTheme.warning),
            onPressed: () async {
              Navigator.pop(ctx);
              setState(() => _isSaving = true);
              final res = await _api.resetStudentFace(widget.student['id']);
              setState(() => _isSaving = false);
              if (res['success'] == true && mounted) {
                ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
                    content: Text('Đã reset Face ID'),
                    backgroundColor: AppTheme.success));
              } else {
                if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(SnackBar(
                      content: Text(res['message'] ?? 'Lỗi reset'),
                      backgroundColor: AppTheme.error));
                }
              }
            },
            child: const Text('Reset', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      appBar: AppBar(
        title: const Text('Sửa Sinh Viên',
            style: TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: Colors.transparent,
        foregroundColor: AppTheme.textPrimary,
        elevation: 0,
        actions: [
          if (_isSaving)
            const Padding(
                padding: EdgeInsets.all(16),
                child: SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(
                        color: AppTheme.secondary, strokeWidth: 2)))
          else
            IconButton(
                icon: const Icon(Icons.check, color: AppTheme.secondary),
                onPressed: _save),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _buildTextField('Họ tên', _nameCtrl, Icons.person,
                  required: true),
              const SizedBox(height: 16),
              _buildTextField('MSSV', _mssvCtrl, Icons.badge, required: true),
              const SizedBox(height: 16),
              _buildTextField('Mã Lớp', _classCtrl, Icons.class_),
              const SizedBox(height: 16),
              _buildTextField('Email', _emailCtrl, Icons.email),
              const SizedBox(height: 16),
              _buildTextField('Số điện thoại', _phoneCtrl, Icons.phone),
              const SizedBox(height: 32),

              // Dangerous Actions Area
              NeuContainer(
                padding: const EdgeInsets.all(16),
                borderRadius: 16,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('Khu vực nguy hiểm',
                        style: TextStyle(
                            color: AppTheme.error,
                            fontWeight: FontWeight.bold)),
                    const SizedBox(height: 16),
                    SizedBox(
                      width: double.infinity,
                      child: OutlinedButton.icon(
                        style: OutlinedButton.styleFrom(
                          foregroundColor: AppTheme.warning,
                          side: const BorderSide(color: AppTheme.warning),
                          padding: const EdgeInsets.symmetric(vertical: 12),
                          shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(12)),
                        ),
                        icon: const Icon(Icons.face_retouching_off),
                        label: const Text('Reset Dữ Liệu Face ID'),
                        onPressed: _isSaving ? null : _confirmResetFace,
                      ),
                    ),
                    const SizedBox(height: 12),
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton.icon(
                        style: ElevatedButton.styleFrom(
                          backgroundColor: AppTheme.error.withValues(alpha: 0.8),
                          foregroundColor: Colors.white,
                          padding: const EdgeInsets.symmetric(vertical: 12),
                          shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(12)),
                        ),
                        icon: const Icon(Icons.delete_forever),
                        label: const Text('Xóa Sinh Viên Này'),
                        onPressed: _isSaving ? null : _confirmDelete,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildTextField(
      String label, TextEditingController controller, IconData icon,
      {bool required = false}) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label,
            style: const TextStyle(
                color: AppTheme.textSecondary,
                fontSize: 13,
                fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),
        NeuContainer(
          borderRadius: 12,
          child: TextFormField(
            controller: controller,
            style: const TextStyle(color: AppTheme.textPrimary),
            validator: (value) {
              if (required && (value == null || value.isEmpty)) {
                return 'Vui lòng nhập $label';
              }
              return null;
            },
            decoration: InputDecoration(
              prefixIcon: Icon(icon, color: AppTheme.secondary, size: 20),
              border: InputBorder.none,
              contentPadding:
                  const EdgeInsets.symmetric(vertical: 16, horizontal: 16),
            ),
          ),
        ),
      ],
    );
  }
}
