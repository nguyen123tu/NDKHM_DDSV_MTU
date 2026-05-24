import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../providers/auth_provider.dart';
import '../services/api_service.dart';
import '../theme/app_theme.dart';

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

  final _oldPwdCtrl = TextEditingController();
  final _newPwdCtrl = TextEditingController();
  final _confirmPwdCtrl = TextEditingController();

  @override
  void initState() {
    super.initState();
    _fetchProfile();
    _fetchFaceGallery();
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
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Lỗi tải thông tin: $e", style: const TextStyle(color: Colors.white)), backgroundColor: AppTheme.error));
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
        title: const Text("Đổi mật khẩu", style: TextStyle(color: AppTheme.textPrimary)),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            _buildDialogTextField(controller: _oldPwdCtrl, label: "Mật khẩu cũ"),
            const SizedBox(height: 12),
            _buildDialogTextField(controller: _newPwdCtrl, label: "Mật khẩu mới"),
            const SizedBox(height: 12),
            _buildDialogTextField(controller: _confirmPwdCtrl, label: "Xác nhận mật khẩu mới"),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text("Hủy", style: TextStyle(color: AppTheme.textSecondary))),
          ElevatedButton(
            onPressed: () async {
              if (_newPwdCtrl.text != _confirmPwdCtrl.text) {
                ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: const Text("Mật khẩu xác nhận không khớp"), backgroundColor: AppTheme.warning));
                return;
              }
              try {
                final res = await _apiService.changePassword(_oldPwdCtrl.text, _newPwdCtrl.text);
                if (mounted) {
                  Navigator.pop(context);
                  ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(res['message']), backgroundColor: AppTheme.success));
                  _oldPwdCtrl.clear(); _newPwdCtrl.clear(); _confirmPwdCtrl.clear();
                }
              } catch (e) {
                ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Lỗi: $e"), backgroundColor: AppTheme.error));
              }
            },
            style: ElevatedButton.styleFrom(backgroundColor: AppTheme.primary),
            child: const Text("Cập nhật"),
          ),
        ],
      ),
    );
  }

  Widget _buildDialogTextField({required TextEditingController controller, required String label}) {
    return TextField(
      controller: controller, 
      obscureText: true, 
      style: const TextStyle(color: AppTheme.textPrimary),
      decoration: InputDecoration(
        labelText: label,
        labelStyle: const TextStyle(color: AppTheme.textSecondary),
        enabledBorder: UnderlineInputBorder(borderSide: BorderSide(color: AppTheme.textSecondary.withOpacity(0.5))),
        focusedBorder: const UnderlineInputBorder(borderSide: BorderSide(color: AppTheme.primary)),
      ),
    );
  }

  Future<void> _pickAndUploadAvatar() async {
    final picker = ImagePicker();
    final pickedFile = await picker.pickImage(source: ImageSource.gallery, imageQuality: 50);

    if (pickedFile != null) {
      if (mounted) setState(() => _isLoading = true);
      try {
        final bytes = await pickedFile.readAsBytes();
        final base64Image = base64Encode(bytes);
        final res = await _apiService.updateAvatar(base64Image);
        
        if (res['success'] == true) {
          await _fetchProfile(); // Refresh data
          if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: const Text("Đã cập nhật ảnh đại diện"), backgroundColor: AppTheme.success));
        } else {
          if (mounted) {
            ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Lỗi: ${res['message']}"), backgroundColor: AppTheme.error));
            setState(() => _isLoading = false);
          }
        }
      } catch (e) {
        if (mounted) {
          setState(() => _isLoading = false);
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Lỗi: $e"), backgroundColor: AppTheme.error));
        }
      }
    }
  }

  void _showEditProfileDialog() {
    if (_profileData == null) return;
    final emailCtrl = TextEditingController(text: _profileData!['email']);
    final sdtCtrl = TextEditingController(text: _profileData!['sdt']);
    final queQuanCtrl = TextEditingController(text: _profileData!['que_quan']);
    final danTocCtrl = TextEditingController(text: _profileData!['dan_toc'] ?? "Kinh");

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: AppTheme.surface,
        title: const Text("Cập nhật thông tin", style: TextStyle(color: AppTheme.textPrimary)),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              _buildDialogTextFieldCustom(controller: emailCtrl, label: "Email"),
              const SizedBox(height: 8),
              _buildDialogTextFieldCustom(controller: sdtCtrl, label: "Số điện thoại"),
              const SizedBox(height: 8),
              _buildDialogTextFieldCustom(controller: queQuanCtrl, label: "Quê quán"),
              const SizedBox(height: 8),
              _buildDialogTextFieldCustom(controller: danTocCtrl, label: "Dân tộc"),
            ],
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text("Hủy", style: TextStyle(color: AppTheme.textSecondary))),
          ElevatedButton(
            onPressed: () async {
              try {
                final res = await _apiService.updateProfile({
                  'email': emailCtrl.text,
                  'sdt': sdtCtrl.text,
                  'que_quan': queQuanCtrl.text,
                  'dan_toc': danTocCtrl.text,
                });
                if (mounted) {
                  Navigator.pop(context);
                  ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(res['message']), backgroundColor: AppTheme.success));
                  _fetchProfile(); // Refresh
                }
              } catch (e) {
                ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Lỗi: $e"), backgroundColor: AppTheme.error));
              }
            },
            style: ElevatedButton.styleFrom(backgroundColor: AppTheme.primary),
            child: const Text("Cập nhật"),
          ),
        ],
      ),
    );
  }

  Widget _buildDialogTextFieldCustom({required TextEditingController controller, required String label}) {
    return TextField(
      controller: controller, 
      style: const TextStyle(color: AppTheme.textPrimary),
      decoration: InputDecoration(
        labelText: label,
        labelStyle: const TextStyle(color: AppTheme.textSecondary),
        enabledBorder: UnderlineInputBorder(borderSide: BorderSide(color: AppTheme.textSecondary.withOpacity(0.5))),
        focusedBorder: const UnderlineInputBorder(borderSide: BorderSide(color: AppTheme.primary)),
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
    if (_isLoading) return const Scaffold(backgroundColor: AppTheme.background, body: Center(child: CircularProgressIndicator(color: AppTheme.secondary)));

    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: AppBar(
        title: const Text("Thông tin cá nhân"),
        actions: [
          if (_profileData != null)
            IconButton(
              icon: const Icon(Icons.edit_note_outlined, color: AppTheme.secondary),
              onPressed: _showEditProfileDialog,
            )
        ],
      ),
      body: Stack(
        children: [
           // Ambient Background Glows
          Positioned(
            top: -100,
            right: -100,
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

          SingleChildScrollView(
            padding: const EdgeInsets.all(20),
            child: Column(
              children: [
                GestureDetector(
                  onTap: _pickAndUploadAvatar,
                  child: Stack(
                    children: [
                      Container(
                        padding: const EdgeInsets.all(4),
                        decoration: AppTheme.glassDecoration(shape: BoxShape.circle, opacity: 0.2),
                        child: CircleAvatar(
                          radius: 50,
                          backgroundColor: AppTheme.surfaceLight,
                          backgroundImage: (_profileData != null && _profileData!['avatar'] != null)
                              ? NetworkImage(_getAvatarUrl(_profileData!['avatar']))
                              : null,
                          child: (_profileData == null || _profileData!['avatar'] == null)
                              ? const Icon(Icons.person, size: 50, color: AppTheme.textSecondary)
                              : null,
                        ),
                      ),
                      Positioned(
                        bottom: 0,
                        right: 0,
                        child: Container(
                          padding: const EdgeInsets.all(6),
                          decoration: BoxDecoration(color: AppTheme.secondary, shape: BoxShape.circle, border: Border.all(color: AppTheme.background, width: 2)),
                          child: const Icon(Icons.camera_alt, size: 16, color: Colors.white),
                        ),
                      ),
                    ],
                  ),
                ).animate().scale(duration: 500.ms, curve: Curves.easeOutBack),
                const SizedBox(height: 24),
                
                _buildInfoCard().animate().fadeIn(delay: 200.ms).slideY(begin: 0.1, end: 0),
                const SizedBox(height: 20),
                
                _buildFaceGallery().animate().fadeIn(delay: 400.ms).slideY(begin: 0.1, end: 0),
                const SizedBox(height: 30),
                
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton.icon(
                    onPressed: _showChangePasswordDialog,
                    icon: const Icon(Icons.lock_reset),
                    label: const Text("Đổi mật khẩu"),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppTheme.surfaceLight,
                      foregroundColor: AppTheme.textPrimary,
                      padding: const EdgeInsets.symmetric(vertical: 16),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                    ),
                  ),
                ).animate().fadeIn(delay: 600.ms).scale(begin: const Offset(0.9, 0.9)),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInfoCard() {
    if (_profileData == null) return const Text("Không có dữ liệu", style: TextStyle(color: AppTheme.textSecondary));
    
    return Container(
      decoration: AppTheme.glassDecoration(borderRadius: 24, opacity: 0.05),
      padding: const EdgeInsets.all(20),
      child: Column(
        children: [
          _infoRow(Icons.badge, "MSSV", _profileData!['mssv'] ?? _profileData!['username']),
          const Divider(color: Colors.white12, height: 24),
          _infoRow(Icons.person, "Họ tên", _profileData!['ho_ten']),
          if (_profileData!['ten_lop'] != null) ...[
            const Divider(color: Colors.white12, height: 24),
            _infoRow(Icons.school, "Lớp", "${_profileData!['ten_lop']} (${_profileData!['ma_lop']})"),
          ],
          const Divider(color: Colors.white12, height: 24),
          _infoRow(Icons.email, "Email", _profileData!['email'] ?? "Chưa cập nhật"),
          const Divider(color: Colors.white12, height: 24),
          _infoRow(Icons.phone, "Số điện thoại", _profileData!['sdt'] ?? "Chưa cập nhật"),
          const Divider(color: Colors.white12, height: 24),
          _infoRow(Icons.calendar_view_day, "Niên khóa", _profileData!['nien_khoa'] ?? "Chưa cập nhật"),
          const Divider(color: Colors.white12, height: 24),
          _infoRow(Icons.flag, "Dân tộc", _profileData!['dan_toc'] ?? "Kinh"),
          const Divider(color: Colors.white12, height: 24),
          _infoRow(Icons.credit_card, "CCCD", _profileData!['cmnd_cccd'] ?? "Chưa cập nhật"),
          const Divider(color: Colors.white12, height: 24),
          _infoRow(Icons.location_on, "Quê quán", _profileData!['que_quan'] ?? "Chưa cập nhật"),
        ],
      ),
    );
  }

  Widget _buildFaceGallery() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: AppTheme.glassDecoration(borderRadius: 24, opacity: 0.05),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text("DỮ LIỆU KHUÔN MẶT (AI)", style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppTheme.textSecondary, letterSpacing: 1)),
              if (_profileData != null && (_profileData!['trang_thai_face'] == 2 || _profileData!['da_train'] == 1))
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(color: AppTheme.success.withOpacity(0.2), borderRadius: BorderRadius.circular(8)),
                  child: const Row(
                    children: [
                      Icon(Icons.verified, color: AppTheme.success, size: 12),
                      SizedBox(width: 4),
                      Text("Đã xác thực", style: TextStyle(color: AppTheme.success, fontSize: 10, fontWeight: FontWeight.bold)),
                    ],
                  ),
                ),
            ],
          ),
          const SizedBox(height: 16),
          SizedBox(
            height: 90,
            child: _loadingGallery
                ? const Center(child: CircularProgressIndicator(color: AppTheme.secondary))
                : _faceImages.isEmpty
                    ? const Center(child: Text("Chưa có ảnh đăng ký", style: TextStyle(fontSize: 13, color: AppTheme.textMuted, fontStyle: FontStyle.italic)))
                    : ListView.builder(
                        scrollDirection: Axis.horizontal,
                        itemCount: _faceImages.length,
                        itemBuilder: (context, index) {
                          return Container(
                            width: 90,
                            margin: const EdgeInsets.only(right: 12),
                            decoration: BoxDecoration(
                              borderRadius: BorderRadius.circular(16),
                              border: Border.all(color: Colors.white.withOpacity(0.1)),
                              image: DecorationImage(
                                image: NetworkImage("${ApiService.baseUrl}/database/${_faceImages[index]}"),
                                fit: BoxFit.cover,
                              ),
                              boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.3), blurRadius: 10)],
                            ),
                          ).animate().scale(delay: Duration(milliseconds: 100 * index));
                        },
                      ),
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
          decoration: BoxDecoration(color: AppTheme.surfaceLight.withOpacity(0.5), shape: BoxShape.circle),
          child: Icon(icon, color: AppTheme.secondary, size: 18),
        ),
        const SizedBox(width: 16),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(label, style: const TextStyle(color: AppTheme.textSecondary, fontSize: 11)),
              const SizedBox(height: 2),
              Text(value, style: const TextStyle(color: AppTheme.textPrimary, fontWeight: FontWeight.bold, fontSize: 14), overflow: TextOverflow.ellipsis),
            ],
          ),
        )
      ],
    );
  }
}
