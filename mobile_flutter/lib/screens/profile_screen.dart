import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:image_picker/image_picker.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../providers/auth_provider.dart';
import '../services/api_service.dart';
import '../theme/app_theme.dart';
import '../widgets/neu_container.dart';
import '../widgets/neu_button.dart';
import 'admin_leave_screen.dart';
import 'student_leave_screen.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  _ProfileScreenState createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  final ApiService _apiService = ApiService();
  Map<String, dynamic>? _profileData;
  bool _isLoading = true;
  List<String> _faceImages = [];
  bool _loadingGallery = true;
  bool _useBiometric = true;

  final _oldPwdCtrl = TextEditingController();
  final _newPwdCtrl = TextEditingController();
  final _confirmPwdCtrl = TextEditingController();

  @override
  void initState() {
    super.initState();
    _fetchProfile();
    _fetchFaceGallery();
    _loadBiometricSettings();
  }

  Future<void> _loadBiometricSettings() async {
    final prefs = await SharedPreferences.getInstance();
    if (mounted) {
      setState(() {
        _useBiometric = prefs.getBool('use_biometric') ?? true;
      });
    }
  }

  Future<void> _toggleBiometric(bool value) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('use_biometric', value);
    if (mounted) {
      setState(() {
        _useBiometric = value;
      });
    }
  }

  Future<void> _fetchProfile() async {
    try {
      final res = await _apiService.getProfile();
      if (mounted) {
        setState(() {
          _profileData = res['data'];
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isLoading = false);
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content: Text("Lỗi tải thông tin: $e",
                style: const TextStyle(color: Colors.white)),
            backgroundColor: AppTheme.error));
      }
    }
  }

  Future<void> _fetchFaceGallery() async {
    try {
      final res = await _apiService.getFaceGallery();
      if (res['success'] == true) {
        setState(() {
          _faceImages = List<String>.from(res['data']);
          _loadingGallery = false;
        });
      }
    } catch (e) {
      if (mounted) setState(() => _loadingGallery = false);
    }
  }

  void _showChangePasswordDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: AppTheme.surface,
        title: const Text("Đổi mật khẩu",
            style: TextStyle(color: AppTheme.textPrimary)),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            _buildDialogTextField(
                controller: _oldPwdCtrl, label: "Mật khẩu cũ"),
            const SizedBox(height: 12),
            _buildDialogTextField(
                controller: _newPwdCtrl, label: "Mật khẩu mới"),
            const SizedBox(height: 12),
            _buildDialogTextField(
                controller: _confirmPwdCtrl, label: "Xác nhận mật khẩu mới"),
          ],
        ),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text("Hủy",
                  style: TextStyle(color: AppTheme.textSecondary))),
          ElevatedButton(
            onPressed: () async {
              if (_newPwdCtrl.text != _confirmPwdCtrl.text) {
                ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
                    content: Text("Mật khẩu xác nhận không khớp"),
                    backgroundColor: AppTheme.warning));
                return;
              }
              try {
                final res = await _apiService.changePassword(
                    _oldPwdCtrl.text, _newPwdCtrl.text);
                if (mounted) {
                  Navigator.pop(context);
                  ScaffoldMessenger.of(context).showSnackBar(SnackBar(
                      content: Text(res['message']),
                      backgroundColor: AppTheme.success));
                  _oldPwdCtrl.clear();
                  _newPwdCtrl.clear();
                  _confirmPwdCtrl.clear();
                }
              } catch (e) {
                ScaffoldMessenger.of(context).showSnackBar(SnackBar(
                    content: Text("Lỗi: $e"), backgroundColor: AppTheme.error));
              }
            },
            style: ElevatedButton.styleFrom(backgroundColor: AppTheme.primary),
            child: const Text("Cập nhật"),
          ),
        ],
      ),
    );
  }

  Widget _buildDialogTextField(
      {required TextEditingController controller, required String label}) {
    return TextField(
      controller: controller,
      obscureText: true,
      style: const TextStyle(color: AppTheme.textPrimary),
      decoration: InputDecoration(
        labelText: label,
        labelStyle: const TextStyle(color: AppTheme.textSecondary),
        enabledBorder: UnderlineInputBorder(
            borderSide:
                BorderSide(color: AppTheme.textSecondary.withValues(alpha: 0.5))),
        focusedBorder: const UnderlineInputBorder(
            borderSide: BorderSide(color: AppTheme.primary)),
      ),
    );
  }

  Future<void> _pickAndUploadAvatar() async {
    final picker = ImagePicker();
    final pickedFile =
        await picker.pickImage(source: ImageSource.gallery, imageQuality: 50);

    if (pickedFile != null) {
      if (mounted) setState(() => _isLoading = true);
      try {
        final bytes = await pickedFile.readAsBytes();
        final base64Image = base64Encode(bytes);
        final res = await _apiService.updateAvatar(base64Image);

        if (res['success'] == true) {
          await _fetchProfile(); // Refresh data
          if (mounted) {
            ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
                content: Text("Đã cập nhật ảnh đại diện"),
                backgroundColor: AppTheme.success));
          }
        } else {
          if (mounted) {
            ScaffoldMessenger.of(context).showSnackBar(SnackBar(
                content: Text("Lỗi: ${res['message']}"),
                backgroundColor: AppTheme.error));
            setState(() => _isLoading = false);
          }
        }
      } catch (e) {
        if (mounted) {
          setState(() => _isLoading = false);
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(
              content: Text("Lỗi: $e"), backgroundColor: AppTheme.error));
        }
      }
    }
  }

  void _showEditProfileDialog() {
    if (_profileData == null) return;

    final bool isAdmin =
        _profileData!['role'] == 'admin' || _profileData!['mssv'] == null;

    final emailCtrl = TextEditingController(text: _profileData!['email'] ?? '');
    final sdtCtrl = TextEditingController(text: _profileData!['sdt'] ?? '');
    final queQuanCtrl =
        TextEditingController(text: _profileData!['que_quan'] ?? '');
    final danTocCtrl =
        TextEditingController(text: _profileData!['dan_toc'] ?? "Kinh");
    final newPwdCtrl = TextEditingController();

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: AppTheme.surface,
        title: const Text("Cập nhật thông tin",
            style: TextStyle(color: AppTheme.textPrimary)),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              if (!isAdmin) ...[
                _buildDialogTextFieldCustom(
                    controller: emailCtrl, label: "Email"),
                const SizedBox(height: 8),
                _buildDialogTextFieldCustom(
                    controller: sdtCtrl, label: "Số điện thoại"),
                const SizedBox(height: 8),
                _buildDialogTextFieldCustom(
                    controller: queQuanCtrl, label: "Quê quán"),
                const SizedBox(height: 8),
                _buildDialogTextFieldCustom(
                    controller: danTocCtrl, label: "Dân tộc"),
                const SizedBox(height: 8),
              ],
              _buildDialogTextFieldCustom(
                  controller: newPwdCtrl,
                  label: "Đổi mật khẩu mới (Tùy chọn)",
                  isPassword: true),
              const Padding(
                padding: EdgeInsets.only(top: 4.0),
                child: Text("Bỏ trống nếu không muốn đổi mật khẩu",
                    style: TextStyle(
                        color: AppTheme.textMuted,
                        fontSize: 11,
                        fontStyle: FontStyle.italic)),
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text("Hủy",
                  style: TextStyle(color: AppTheme.textSecondary))),
          ElevatedButton(
            onPressed: () async {
              try {
                final res = await _apiService.updateProfile({
                  'email': emailCtrl.text,
                  'sdt': sdtCtrl.text,
                  'que_quan': queQuanCtrl.text,
                  'dan_toc': danTocCtrl.text,
                  if (newPwdCtrl.text.trim().isNotEmpty)
                    'new_password': newPwdCtrl.text.trim(),
                });
                if (mounted) {
                  Navigator.pop(context);
                  ScaffoldMessenger.of(context).showSnackBar(SnackBar(
                      content: Text(res['message']),
                      backgroundColor: AppTheme.success));
                  _fetchProfile(); // Refresh
                }
              } catch (e) {
                ScaffoldMessenger.of(context).showSnackBar(SnackBar(
                    content: Text("Lỗi: $e"), backgroundColor: AppTheme.error));
              }
            },
            style: ElevatedButton.styleFrom(backgroundColor: AppTheme.primary),
            child: const Text("Cập nhật"),
          ),
        ],
      ),
    );
  }

  Widget _buildDialogTextFieldCustom(
      {required TextEditingController controller,
      required String label,
      bool isPassword = false}) {
    return TextField(
      controller: controller,
      obscureText: isPassword,
      style: const TextStyle(color: AppTheme.textPrimary),
      decoration: InputDecoration(
        labelText: label,
        labelStyle: const TextStyle(color: AppTheme.textSecondary),
        enabledBorder: UnderlineInputBorder(
            borderSide:
                BorderSide(color: AppTheme.textSecondary.withValues(alpha: 0.5))),
        focusedBorder: const UnderlineInputBorder(
            borderSide: BorderSide(color: AppTheme.primary)),
      ),
    );
  }

  String _getAvatarUrl(String? avatarPath) {
    if (avatarPath == null || avatarPath.isEmpty) return "";
    if (avatarPath.startsWith("uploads/")) {
      return "${ApiService.baseUrl}/static/$avatarPath";
    }
    return "${ApiService.baseUrl}/database/$avatarPath";
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Scaffold(
          backgroundColor: AppTheme.background,
          body: Center(
              child: CircularProgressIndicator(color: AppTheme.secondary)));
    }

    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      appBar: AppBar(
        title: const Text("Thông tin cá nhân"),
        actions: [
          if (_profileData != null)
            IconButton(
              icon: const Icon(Icons.edit_note_outlined,
                  color: AppTheme.secondary),
              onPressed: _showEditProfileDialog,
            )
        ],
      ),
      body: Stack(
        children: [
          Container(color: Theme.of(context).scaffoldBackgroundColor),

          SingleChildScrollView(
            padding: const EdgeInsets.all(20),
            child: Column(
              children: [
                GestureDetector(
                  onTap: _pickAndUploadAvatar,
                  child: Stack(
                    children: [
                      NeuContainer(
                        padding: const EdgeInsets.all(4),
                        shape: BoxShape.circle,
                        child: CircleAvatar(
                          radius: 50,
                          backgroundColor: AppTheme.surfaceLight,
                          backgroundImage: (_profileData != null &&
                                  _profileData!['avatar'] != null)
                              ? NetworkImage(
                                  _getAvatarUrl(_profileData!['avatar']))
                              : null,
                          child: (_profileData == null ||
                                  _profileData!['avatar'] == null)
                              ? const Icon(Icons.person,
                                  size: 50, color: AppTheme.textSecondary)
                              : null,
                        ),
                      ),
                      Positioned(
                        bottom: 0,
                        right: 0,
                        child: Container(
                          padding: const EdgeInsets.all(6),
                          decoration: BoxDecoration(
                              color: AppTheme.secondary,
                              shape: BoxShape.circle,
                              border: Border.all(
                                  color: AppTheme.background, width: 2)),
                          child: const Icon(Icons.camera_alt,
                              size: 16, color: Colors.white),
                        ),
                      ),
                    ],
                  ),
                ).animate().scale(duration: 500.ms, curve: Curves.easeOutBack),
                const SizedBox(height: 24),
                _buildInfoCard()
                    .animate()
                    .fadeIn(delay: 200.ms)
                    .slideY(begin: 0.1, end: 0),
                const SizedBox(height: 20),
                if (_profileData == null ||
                    (_profileData!['role'] != 'admin' &&
                        _profileData!['mssv'] != null)) ...[
                  _buildFaceGallery()
                      .animate()
                      .fadeIn(delay: 400.ms)
                      .slideY(begin: 0.1, end: 0),
                  const SizedBox(height: 20),
                ],
                _buildSettingsCard()
                    .animate()
                    .fadeIn(delay: 500.ms)
                    .slideY(begin: 0.1, end: 0),
                const SizedBox(height: 16),
                
                // NÚT XIN PHÉP VẮNG MẶT / QUẢN LÝ ĐƠN TỪ
                SizedBox(
                  width: double.infinity,
                  child: NeuButton(
                    onPressed: () {
                      final bool isAdmin = _profileData!['role'] == 'admin' || _profileData!['mssv'] == null;
                      if (isAdmin) {
                        Navigator.push(
                          context,
                          MaterialPageRoute(builder: (context) {
                            return const AdminLeaveScreen();
                          }),
                        );
                      } else {
                        Navigator.push(
                          context,
                          MaterialPageRoute(builder: (context) {
                            return const StudentLeaveScreen();
                          }),
                        );
                      }
                    },
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(
                          (_profileData != null && (_profileData!['role'] == 'admin' || _profileData!['mssv'] == null)) 
                              ? Icons.assignment 
                              : Icons.edit_document, 
                          color: AppTheme.secondary
                        ),
                        const SizedBox(width: 8),
                        Text(
                          (_profileData != null && (_profileData!['role'] == 'admin' || _profileData!['mssv'] == null)) 
                              ? "Quản lý Đơn vắng mặt" 
                              : "Xin phép vắng mặt", 
                          style: const TextStyle(color: AppTheme.secondary, fontWeight: FontWeight.bold)
                        ),
                      ],
                    ),
                  ),
                ).animate().fadeIn(delay: 550.ms).scale(begin: const Offset(0.9, 0.9)),
                
                const SizedBox(height: 30),
                SizedBox(
                  width: double.infinity,
                  child: NeuButton(
                    onPressed: _showChangePasswordDialog,
                    child: const Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.lock_reset, color: AppTheme.textPrimary),
                        SizedBox(width: 8),
                        Text("Đổi mật khẩu", style: TextStyle(color: AppTheme.textPrimary, fontWeight: FontWeight.bold)),
                      ],
                    ),
                  ),
                )
                    .animate()
                    .fadeIn(delay: 600.ms)
                    .scale(begin: const Offset(0.9, 0.9)),
                const SizedBox(height: 16),
                SizedBox(
                  width: double.infinity,
                  child: NeuButton(
                    onPressed: () async {
                      final auth =
                          Provider.of<AuthProvider>(context, listen: false);
                      await auth.logout();
                      if (mounted) {
                        Navigator.of(context)
                            .pushNamedAndRemoveUntil('/', (route) => false);
                      }
                    },
                    child: const Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.logout, color: AppTheme.error),
                        SizedBox(width: 8),
                        Text("Đăng xuất", style: TextStyle(color: AppTheme.error, fontWeight: FontWeight.bold)),
                      ],
                    ),
                  ),
                )
                    .animate()
                    .fadeIn(delay: 700.ms)
                    .scale(begin: const Offset(0.9, 0.9)),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInfoCard() {
    if (_profileData == null) {
      return const Text("Không có dữ liệu",
          style: TextStyle(color: AppTheme.textSecondary));
    }

    final bool isAdmin =
        _profileData!['role'] == 'admin' || _profileData!['mssv'] == null;

    return NeuContainer(
      borderRadius: 24,
      padding: const EdgeInsets.all(20),
      child: Column(
        children: [
          if (isAdmin) ...[
            _infoRow(Icons.admin_panel_settings, "Tài khoản",
                _profileData!['username'] ?? "Admin"),
            const Divider(color: Colors.white12, height: 24),
            _infoRow(Icons.person, "Họ tên",
                _profileData!['ho_ten'] ?? "Quản trị viên"),
            const Divider(color: Colors.white12, height: 24),
            _infoRow(Icons.security, "Quyền", "Quản trị hệ thống"),
          ] else ...[
            _infoRow(Icons.badge, "MSSV",
                _profileData!['mssv'] ?? _profileData!['username']),
            const Divider(color: Colors.white12, height: 24),
            _infoRow(Icons.person, "Họ tên", _profileData!['ho_ten'] ?? ""),
            if (_profileData!['ten_lop'] != null) ...[
              const Divider(color: Colors.white12, height: 24),
              _infoRow(Icons.school, "Lớp",
                  "${_profileData!['ten_lop']} (${_profileData!['ma_lop']})"),
            ],
            const Divider(color: Colors.white12, height: 24),
            _infoRow(Icons.email, "Email",
                _profileData!['email'] ?? "Chưa cập nhật"),
            const Divider(color: Colors.white12, height: 24),
            _infoRow(Icons.phone, "Số điện thoại",
                _profileData!['sdt'] ?? "Chưa cập nhật"),
            const Divider(color: Colors.white12, height: 24),
            _infoRow(Icons.calendar_view_day, "Niên khóa",
                _profileData!['nien_khoa'] ?? "Chưa cập nhật"),
            const Divider(color: Colors.white12, height: 24),
            _infoRow(Icons.flag, "Dân tộc", _profileData!['dan_toc'] ?? "Kinh"),
            const Divider(color: Colors.white12, height: 24),
            _infoRow(Icons.credit_card, "CCCD",
                _profileData!['cmnd_cccd'] ?? "Chưa cập nhật"),
            const Divider(color: Colors.white12, height: 24),
            _infoRow(Icons.location_on, "Quê quán",
                _profileData!['que_quan'] ?? "Chưa cập nhật"),
          ]
        ],
      ),
    );
  }

  Widget _buildFaceGallery() {
    return NeuContainer(
      borderRadius: 24,
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text("DỮ LIỆU KHUÔN MẶT (AI)",
                  style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                      color: AppTheme.textSecondary,
                      letterSpacing: 1)),
              if (_profileData != null &&
                  (_profileData!['trang_thai_face'] == 2 ||
                      _profileData!['da_train'] == 1))
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                      color: AppTheme.success.withValues(alpha: 0.2),
                      borderRadius: BorderRadius.circular(8)),
                  child: const Row(
                    children: [
                      Icon(Icons.verified, color: AppTheme.success, size: 12),
                      SizedBox(width: 4),
                      Text("Đã xác thực",
                          style: TextStyle(
                              color: AppTheme.success,
                              fontSize: 10,
                              fontWeight: FontWeight.bold)),
                    ],
                  ),
                ),
            ],
          ),
          const SizedBox(height: 16),
          SizedBox(
            height: 90,
            child: _loadingGallery
                ? const Center(
                    child: CircularProgressIndicator(color: AppTheme.secondary))
                : _faceImages.isEmpty
                    ? const Center(
                        child: Text("Chưa có ảnh đăng ký",
                            style: TextStyle(
                                fontSize: 13,
                                color: AppTheme.textMuted,
                                fontStyle: FontStyle.italic)))
                    : ListView.builder(
                        scrollDirection: Axis.horizontal,
                        itemCount: _faceImages.length,
                        itemBuilder: (context, index) {
                          return Container(
                            width: 90,
                            margin: const EdgeInsets.only(right: 12),
                            decoration: BoxDecoration(
                              borderRadius: BorderRadius.circular(16),
                              border: Border.all(
                                  color: Colors.white.withValues(alpha: 0.1)),
                              image: DecorationImage(
                                image: NetworkImage(
                                    "${ApiService.baseUrl}/database/${_faceImages[index]}"),
                                fit: BoxFit.cover,
                              ),
                              boxShadow: [
                                BoxShadow(
                                    color: Colors.black.withValues(alpha: 0.3),
                                    blurRadius: 10)
                              ],
                            ),
                          ).animate().scale(
                              delay: Duration(milliseconds: 100 * index));
                        },
                      ),
          ),
        ],
      ),
    );
  }

  Widget _buildSettingsCard() {
    return NeuContainer(
      borderRadius: 24,
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                    color: AppTheme.surfaceLight.withValues(alpha: 0.5),
                    shape: BoxShape.circle),
                child: const Icon(Icons.fingerprint,
                    color: AppTheme.secondary, size: 20),
              ),
              const SizedBox(width: 16),
              const Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text("Đăng nhập Sinh trắc học",
                      style: TextStyle(
                          color: AppTheme.textPrimary,
                          fontWeight: FontWeight.bold,
                          fontSize: 14)),
                  SizedBox(height: 2),
                  Text("Dùng Vân tay / Face ID",
                      style: TextStyle(
                          color: AppTheme.textSecondary, fontSize: 11)),
                ],
              ),
            ],
          ),
          Switch(
            value: _useBiometric,
            activeThumbColor: AppTheme.secondary,
            onChanged: _toggleBiometric,
          ),
        ],
      ),
    );
  }

  Widget _infoRow(IconData icon, String label, String value) {
    return Row(
      children: [
        Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
              color: AppTheme.surfaceLight.withValues(alpha: 0.5),
              shape: BoxShape.circle),
          child: Icon(icon, color: AppTheme.secondary, size: 18),
        ),
        const SizedBox(width: 16),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(label,
                  style: const TextStyle(
                      color: AppTheme.textSecondary, fontSize: 11)),
              const SizedBox(height: 2),
              Text(value,
                  style: const TextStyle(
                      color: AppTheme.textPrimary,
                      fontWeight: FontWeight.bold,
                      fontSize: 14),
                  overflow: TextOverflow.ellipsis),
            ],
          ),
        )
      ],
    );
  }
}
