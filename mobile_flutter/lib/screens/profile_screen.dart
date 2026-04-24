
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import '../providers/auth_provider.dart';
import '../services/api_service.dart';

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
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Lỗi tải thông tin: $e")));
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
        title: const Text("Đổi mật khẩu"),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(controller: _oldPwdCtrl, obscureText: true, decoration: const InputDecoration(labelText: "Mật khẩu cũ")),
            TextField(controller: _newPwdCtrl, obscureText: true, decoration: const InputDecoration(labelText: "Mật khẩu mới")),
            TextField(controller: _confirmPwdCtrl, obscureText: true, decoration: const InputDecoration(labelText: "Xác nhận mật khẩu mới")),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text("Hủy")),
          ElevatedButton(
            onPressed: () async {
              if (_newPwdCtrl.text != _confirmPwdCtrl.text) {
                ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Mật khẩu xác nhận không khớp")));
                return;
              }
              try {
                final res = await _apiService.changePassword(_oldPwdCtrl.text, _newPwdCtrl.text);
                if (mounted) {
                  Navigator.pop(context);
                  ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(res['message'])));
                  _oldPwdCtrl.clear(); _newPwdCtrl.clear(); _confirmPwdCtrl.clear();
                }
              } catch (e) {
                ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Lỗi: $e")));
              }
            },
            child: const Text("Cập nhật"),
          ),
        ],
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
          if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Đã cập nhật ảnh đại diện")));
        } else {
          if (mounted) {
            ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Lỗi: ${res['message']}")));
            setState(() => _isLoading = false);
          }
        }
      } catch (e) {
        if (mounted) {
          setState(() => _isLoading = false);
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Lỗi: $e")));
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
        title: const Text("Cập nhật thông tin"),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(controller: emailCtrl, decoration: const InputDecoration(labelText: "Email")),
              TextField(controller: sdtCtrl, decoration: const InputDecoration(labelText: "Số điện thoại")),
              TextField(controller: queQuanCtrl, decoration: const InputDecoration(labelText: "Quê quán")),
              TextField(controller: danTocCtrl, decoration: const InputDecoration(labelText: "Dân tộc")),
            ],
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text("Hủy")),
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
                  ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(res['message'])));
                  _fetchProfile(); // Refresh
                }
              } catch (e) {
                ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Lỗi: $e")));
              }
            },
            child: const Text("Cập nhật"),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) return const Scaffold(body: Center(child: CircularProgressIndicator()));

    return Scaffold(
      appBar: AppBar(
        title: const Text("Thông tin cá nhân"),
        backgroundColor: const Color(0xFF1B3A5C),
        foregroundColor: Colors.white,
        actions: [
          if (_profileData != null)
            IconButton(
              icon: const Icon(Icons.edit_note_outlined),
              onPressed: _showEditProfileDialog,
            )
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          children: [
            GestureDetector(
              onTap: _pickAndUploadAvatar,
              child: Stack(
                children: [
                  CircleAvatar(
                    radius: 50,
                    backgroundColor: const Color(0xFF1B3A5C),
                    backgroundImage: (_profileData != null && _profileData!['avatar'] != null)
                        ? NetworkImage("${ApiService.baseUrl}/static/${_profileData!['avatar']}")
                        : null,
                    child: (_profileData == null || _profileData!['avatar'] == null)
                        ? const Icon(Icons.person, size: 50, color: Colors.white)
                        : null,
                  ),
                  Positioned(
                    bottom: 0,
                    right: 0,
                    child: Container(
                      padding: const EdgeInsets.all(4),
                      decoration: const BoxDecoration(color: Color(0xFF2E96EB), shape: BoxShape.circle),
                      child: const Icon(Icons.camera_alt, size: 18, color: Colors.white),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),
            _buildInfoCard(),
            const SizedBox(height: 20),
            _buildFaceGallery(),
            const SizedBox(height: 30),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: _showChangePasswordDialog,
                icon: const Icon(Icons.lock_reset),
                label: const Text("Đổi mật khẩu"),
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF2E96EB),
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 12),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildInfoCard() {
    if (_profileData == null) return const Text("Không có dữ liệu");
    
    return Card(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            _infoRow(Icons.badge, "MSSV", _profileData!['mssv'] ?? _profileData!['username']),
            const Divider(),
            _infoRow(Icons.person, "Họ tên", _profileData!['ho_ten']),
            const Divider(),
            if (_profileData!['ten_lop'] != null) ...[
              _infoRow(Icons.school, "Lớp", "${_profileData!['ten_lop']} (${_profileData!['ma_lop']})"),
              const Divider(),
            ],
            _infoRow(Icons.email, "Email", _profileData!['email'] ?? "Chưa cập nhật"),
            const Divider(),
            _infoRow(Icons.phone, "Số điện thoại", _profileData!['sdt'] ?? "Chưa cập nhật"),
            const Divider(),
            _infoRow(Icons.calendar_view_day, "Niên khóa", _profileData!['nien_khoa'] ?? "Chưa cập nhật"),
            const Divider(),
            _infoRow(Icons.flag, "Dân tộc", _profileData!['dan_toc'] ?? "Kinh"),
            const Divider(),
            _infoRow(Icons.credit_card, "CCCD", _profileData!['cmnd_cccd'] ?? "Chưa cập nhật"),
            const Divider(),
            _infoRow(Icons.location_on, "Quê quán", _profileData!['que_quan'] ?? "Chưa cập nhật"),
          ],
        ),
      ),
    );
  }

  Widget _buildFaceGallery() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(15),
        boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.02), blurRadius: 10)],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text("DỮ LIỆU KHUÔN MẶT (AI)", style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.grey)),
              if (_profileData != null && (_profileData!['trang_thai_face'] == 2 || _profileData!['da_train'] == 1))
                const Row(
                  children: [
                    Icon(Icons.verified, color: Colors.blue, size: 14),
                    SizedBox(width: 4),
                    Text("Đã xác thực", style: TextStyle(color: Colors.blue, fontSize: 11, fontWeight: FontWeight.bold)),
                  ],
                ),
            ],
          ),
          const SizedBox(height: 12),
          SizedBox(
            height: 80,
            child: _loadingGallery
                ? const Center(child: CircularProgressIndicator())
                : _faceImages.isEmpty
                    ? const Center(child: Text("Chưa có ảnh đăng ký", style: TextStyle(fontSize: 12, color: Colors.grey)))
                    : ListView.builder(
                        scrollDirection: Axis.horizontal,
                        itemCount: _faceImages.length,
                        itemBuilder: (context, index) {
                          return Container(
                            width: 80,
                            margin: const EdgeInsets.only(right: 10),
                            decoration: BoxDecoration(
                              borderRadius: BorderRadius.circular(12),
                              border: Border.all(color: Colors.grey.withOpacity(0.1)),
                              image: DecorationImage(
                                image: NetworkImage("${ApiService.baseUrl}/database/${_faceImages[index]}"),
                                fit: BoxFit.cover,
                              ),
                            ),
                          );
                        },
                      ),
          ),
        ],
      ),
    );
  }

  Widget _infoRow(IconData icon, String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        children: [
          Icon(icon, color: const Color(0xFF1B3A5C), size: 20),
          const SizedBox(width: 15),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(label, style: const TextStyle(color: Colors.grey, fontSize: 12)),
                Text(value, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14), overflow: TextOverflow.ellipsis),
              ],
            ),
          )
        ],
      ),
    );
  }
}
