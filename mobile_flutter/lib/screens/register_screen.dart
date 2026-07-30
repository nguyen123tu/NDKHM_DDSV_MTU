import 'dart:convert';
import 'dart:ui';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:flutter_image_compress/flutter_image_compress.dart';
import 'package:camera/camera.dart';
import 'package:provider/provider.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../services/api_service.dart';
import '../providers/auth_provider.dart';
import '../theme/app_theme.dart';
import '../widgets/neu_container.dart';
import '../widgets/neu_button.dart';

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});

  @override
  _RegisterScreenState createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _mssvCtrl = TextEditingController();
  final _nameCtrl = TextEditingController();
  final _emailCtrl = TextEditingController();
  final _sdtCtrl = TextEditingController();

  DateTime? _selectedDate;
  int? _selectedGender = 1;

  bool _isLoadingClasses = true;
  List<dynamic> _classes = [];
  int? _selectedLopId;

  CameraController? _controller;
  List<CameraDescription>? _cameras;
  bool _isCameraReady = false;
  bool _isRegistering = false;
  int _currentStep = 0; // 0: Thông tin, 1: Camera
  final List<String> _capturedImages = [];

  final ApiService _apiService = ApiService();

  @override
  void initState() {
    super.initState();
    _initCamera();
    _loadClasses();
    _prefillUserInfo();
  }

  void _prefillUserInfo() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final auth = Provider.of<AuthProvider>(context, listen: false);
      if (auth.user != null) {
        setState(() {
          _mssvCtrl.text = auth.user!.username;
          _nameCtrl.text = auth.user!.name;
        });
      }
    });
  }

  Future<void> _loadClasses() async {
    setState(() {
      _isLoadingClasses = true;
    });
    try {
      final classes = await _apiService.getClasses();
      if (mounted) {
        setState(() {
          _classes = classes;
          _isLoadingClasses = false;
          if (_classes.isNotEmpty) {
            _selectedLopId = _classes.first['id'];
          }
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isLoadingClasses = false;
        });
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text("Lỗi tải danh sách lớp: $e")));
      }
    }
  }

  Future<void> _initCamera() async {
    try {
      _cameras = await availableCameras();
      if (_cameras != null && _cameras!.isNotEmpty) {
        final frontCamera = _cameras!.firstWhere(
          (c) => c.lensDirection == CameraLensDirection.front,
          orElse: () => _cameras![0],
        );
        _controller = CameraController(frontCamera, ResolutionPreset.medium, enableAudio: false);
        await _controller!.initialize();
        if (!mounted) return;
        setState(() => _isCameraReady = true);
      } else {
        throw Exception("Không tìm thấy camera trên thiết bị");
      }
    } catch (e) {
      if (!mounted) return;
      showDialog(
        context: context,
        builder: (c) => AlertDialog(
          backgroundColor: AppTheme.surfaceLight,
          title:
              const Text("Lỗi Camera", style: TextStyle(color: Colors.white)),
          content: Text("Không thể khởi động camera. Lỗi: $e",
              style: const TextStyle(color: AppTheme.textSecondary)),
          actions: [
            TextButton(
                onPressed: () => Navigator.pop(c),
                child: const Text("Đóng",
                    style: TextStyle(color: AppTheme.primary)))
          ],
        ),
      );
    }
  }

  @override
  void dispose() {
    _controller?.dispose();
    super.dispose();
  }

  // Giới hạn: tối thiểu 5 ảnh, tối đa 20 ảnh
  static const int _minPhotos = 5;
  static const int _maxPhotos = 20;

  // Hướng dẫn chụp từng góc
  static const List<String> _poseGuides = [
    '📷 Nhìn thẳng vào camera',
    '👈 Quay mặt sang TRÁI ~30°',
    '👉 Quay mặt sang PHẢI ~30°',
    '👆 Ngước mặt lên trên ~20°',
    '👇 Cúi mặt xuống dưới ~20°',
    '😊 Nhìn thẳng + CƯỜI',
    '😐 Nhìn thẳng + Không cười',
    '👈 Nghiêng đầu sang TRÁI',
    '👉 Nghiêng đầu sang PHẢI',
    '🔄 Quay trái ~45° (nửa mặt)',
    '🔄 Quay phải ~45° (nửa mặt)',
    '💡 Che sáng 1 bên mặt (tay)',
    '👓 Đeo/Không đeo kính (nếu có)',
    '📷 Nhìn thẳng - lùi xa hơn',
    '📷 Nhìn thẳng - lại gần hơn',
    '😊 Quay trái + Cười',
    '😊 Quay phải + Cười',
    '👆 Ngước lên + nghiêng trái',
    '👇 Cúi xuống + nghiêng phải',
    '📷 Nhìn thẳng - ảnh cuối',
  ];

  String get _currentPoseGuide {
    if (_capturedImages.length >= _poseGuides.length) {
      return '📷 Chụp thêm tùy ý';
    }
    return _poseGuides[_capturedImages.length];
  }

  Future<void> _takeSinglePicture() async {
    if (_controller == null || !_controller!.value.isInitialized) return;
    if (_capturedImages.length >= _maxPhotos) return;
    try {
      final image = await _controller!.takePicture();
      final bytes = await image.readAsBytes();
      setState(() {
        _capturedImages.add(base64Encode(bytes));
      });
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text("Lỗi chụp ảnh: $e")));
      }
    }
  }

  Future<void> _submitRegistration() async {
    if (_mssvCtrl.text.isEmpty || _nameCtrl.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("Vui lòng nhập đủ thông tin!")));
      return;
    }

    if (_selectedLopId == null) {
      ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("Vui lòng chọn lớp học!")));
      return;
    }

    if (_capturedImages.length < _minPhotos) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text(
              "Vui lòng chụp tối thiểu $_minPhotos ảnh! (Đã chụp ${_capturedImages.length}/$_minPhotos)")));
      return;
    }

    setState(() => _isRegistering = true);

    try {
      List<String> base64List = [];
      for (String b64 in _capturedImages) {
        final Uint8List imageBytes = base64Decode(b64);
        try {
          final Uint8List compressedBytes =
              await FlutterImageCompress.compressWithList(
            imageBytes,
            minHeight: 1080,
            minWidth: 1080,
            quality: 70,
          );
          base64List.add(
              "data:image/jpeg;base64,${base64Encode(compressedBytes ?? imageBytes)}");
        } catch (e) {
          base64List.add("data:image/jpeg;base64,$b64");
        }
      }

      final result = await _apiService.registerFace(
          _mssvCtrl.text.trim(),
          _nameCtrl.text.trim(), 
          _selectedLopId!, 
          base64List,
          email: _emailCtrl.text.trim(),
          sdt: _sdtCtrl.text.trim(),
          ngaySinh: _selectedDate != null ? "${_selectedDate!.year}-${_selectedDate!.month.toString().padLeft(2, '0')}-${_selectedDate!.day.toString().padLeft(2, '0')}" : null,
          gioiTinh: _selectedGender,
      );
      if (!mounted) return;

      if (result['success'] == true) {
        showDialog(
          context: context,
          builder: (c) => AlertDialog(
            backgroundColor: AppTheme.surfaceLight,
            shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(16),
                side: const BorderSide(color: Colors.white10)),
            title: Row(children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                    color: Colors.greenAccent.withValues(alpha: 0.1),
                    shape: BoxShape.circle),
                child: const Icon(Icons.check_circle,
                    color: Colors.greenAccent, size: 28),
              ),
              const SizedBox(width: 12),
              const Text("Thành công!", style: TextStyle(color: Colors.white)),
            ]),
            content: Text(result['message'],
                style: const TextStyle(color: AppTheme.textSecondary)),
            actions: [
              TextButton(
                onPressed: () {
                  Navigator.pop(c);
                  Navigator.pop(context);
                },
                child:
                    const Text("OK", style: TextStyle(color: AppTheme.primary)),
              )
            ],
          ),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
              content: Text("Lỗi: ${result['message']}"),
              backgroundColor: Colors.redAccent),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
              content: Text("Lỗi phần cứng/mạng: $e"),
              backgroundColor: Colors.redAccent),
        );
      }
    } finally {
      if (mounted) setState(() => _isRegistering = false);
    }
  }

  Widget _buildInputField(
      {required TextEditingController controller,
      required String label,
      required IconData icon,
      bool readOnly = false}) {
    return NeuContainer(
      isPressed: true,
      borderRadius: 12,
      child: TextField(
        controller: controller,
        readOnly: readOnly,
        style: TextStyle(
            color: readOnly ? AppTheme.textMuted : AppTheme.textPrimary),
        decoration: InputDecoration(
          labelText: label,
          labelStyle:
              const TextStyle(color: AppTheme.textSecondary, fontSize: 14),
          prefixIcon: Icon(icon, color: AppTheme.primary, size: 22),
          filled: false,
          border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide.none),
          contentPadding:
              const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final isStudent =
        Provider.of<AuthProvider>(context, listen: false).user?.role ==
            'student';

    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      appBar: AppBar(
        title: const Text("Đăng ký Khuôn mặt",
            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
        backgroundColor: Colors.transparent,
        foregroundColor: AppTheme.textPrimary,
        elevation: 0,
        leading: _currentStep == 1 
          ? IconButton(
              icon: const Icon(Icons.arrow_back),
              onPressed: () => setState(() => _currentStep = 0),
            ) 
          : const BackButton(),
        actions: [
          if (_currentStep == 1)
            Container(
            margin: const EdgeInsets.only(right: 16, top: 10, bottom: 10),
            padding: const EdgeInsets.symmetric(horizontal: 12),
            decoration: BoxDecoration(
              color: _capturedImages.length >= _minPhotos
                  ? Colors.greenAccent.withValues(alpha: 0.2)
                  : AppTheme.surfaceLight,
              borderRadius: BorderRadius.circular(20),
              border: Border.all(
                  color: _capturedImages.length >= _minPhotos
                      ? Colors.greenAccent.withValues(alpha: 0.5)
                      : Colors.white10),
            ),
            child: Center(
              child: Text(
                "${_capturedImages.length}/$_maxPhotos ảnh",
                style: TextStyle(
                    color: _capturedImages.length >= _minPhotos
                        ? Colors.greenAccent
                        : AppTheme.textSecondary,
                    fontWeight: FontWeight.bold,
                    fontSize: 13),
              ),
            ),
          ),
        ],
      ),
      body: Stack(
        children: [
          // Background - Clean Neumorphism
          Container(color: Theme.of(context).scaffoldBackgroundColor),

          SingleChildScrollView(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Thanh tiến trình
                Padding(
                  padding: const EdgeInsets.only(bottom: 20),
                  child: Row(
                    children: [
                      Expanded(
                        child: Container(
                          height: 4,
                          decoration: BoxDecoration(
                            color: AppTheme.primary,
                            borderRadius: BorderRadius.circular(2),
                          ),
                        ),
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Container(
                          height: 4,
                          decoration: BoxDecoration(
                            color: _currentStep >= 1 ? AppTheme.primary : Colors.white10,
                            borderRadius: BorderRadius.circular(2),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),

                if (_currentStep == 0) ...[
                  // Form card
                  NeuContainer(
                  padding: const EdgeInsets.all(20),
                  borderRadius: 16,
                  child: Column(
                    children: [
                      _buildInputField(
                        controller: _mssvCtrl,
                        label: "Mã Sinh Viên (MSSV)",
                        icon: Icons.badge,
                        readOnly: isStudent,
                      ),
                      const SizedBox(height: 16),
                      _buildInputField(
                        controller: _nameCtrl,
                        label: "Họ và Tên",
                        icon: Icons.person,
                        readOnly: isStudent,
                      ),
                      const SizedBox(height: 16),
                      // Dropdown
                      if (_isLoadingClasses)
                        const Padding(
                          padding: EdgeInsets.all(16),
                          child: Center(
                              child: CircularProgressIndicator(
                                  color: AppTheme.primary, strokeWidth: 2)),
                        )
                      else if (_classes.isEmpty)
                        const Padding(
                          padding: EdgeInsets.all(16),
                          child: Center(
                            child: Text(
                              "Không có lớp học nào.",
                              style: TextStyle(color: Colors.redAccent),
                            ),
                          ),
                        )
                      else
                        IgnorePointer(
                          ignoring: isStudent,
                          child: DropdownButtonFormField<int>(
                            decoration: InputDecoration(
                              labelText: "Lớp Học",
                              labelStyle: const TextStyle(
                                  color: AppTheme.textSecondary, fontSize: 14),
                              prefixIcon: const Icon(Icons.school,
                                  color: AppTheme.primary, size: 22),
                              filled: true,
                              fillColor: isStudent
                                  ? Colors.white.withValues(alpha: 0.02)
                                  : Colors.white.withValues(alpha: 0.05),
                              border: OutlineInputBorder(
                                  borderRadius: BorderRadius.circular(12),
                                  borderSide: BorderSide.none),
                              enabledBorder: OutlineInputBorder(
                                  borderRadius: BorderRadius.circular(12),
                                  borderSide:
                                      const BorderSide(color: Colors.white10)),
                              focusedBorder: OutlineInputBorder(
                                  borderRadius: BorderRadius.circular(12),
                                  borderSide: const BorderSide(
                                      color: AppTheme.primary, width: 1.5)),
                            ),
                            dropdownColor: AppTheme.surfaceLight,
                            initialValue: _selectedLopId,
                            style: TextStyle(
                                color: isStudent
                                    ? AppTheme.textMuted
                                    : AppTheme.textPrimary,
                                fontSize: 15),
                            items: _classes
                                .map<DropdownMenuItem<int>>((dynamic c) {
                              return DropdownMenuItem<int>(
                                  value: c['id'] as int,
                                  child:
                                      Text("${c['ten_lop']} (${c['ma_lop']})"));
                            }).toList(),
                            onChanged: (int? newValue) {
                              setState(() {
                                _selectedLopId = newValue;
                              });
                            },
                          ),
                        ),
                      const SizedBox(height: 16),
                      _buildInputField(
                        controller: _emailCtrl,
                        label: "Email",
                        icon: Icons.email,
                      ),
                      const SizedBox(height: 16),
                      _buildInputField(
                        controller: _sdtCtrl,
                        label: "Số Điện Thoại",
                        icon: Icons.phone,
                      ),
                      const SizedBox(height: 16),
                      // Ngày sinh DatePicker
                      GestureDetector(
                        onTap: () async {
                          final date = await showDatePicker(
                            context: context,
                            initialDate: _selectedDate ?? DateTime(2000),
                            firstDate: DateTime(1950),
                            lastDate: DateTime.now(),
                          );
                          if (date != null) {
                            setState(() => _selectedDate = date);
                          }
                        },
                        child: NeuContainer(
                          isPressed: true,
                          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                          borderRadius: 12,
                          child: Row(
                            children: [
                              const Icon(Icons.calendar_today, color: AppTheme.primary, size: 22),
                              const SizedBox(width: 12),
                              Text(
                                _selectedDate == null 
                                  ? "Ngày Sinh" 
                                  : "${_selectedDate!.day.toString().padLeft(2, '0')}/${_selectedDate!.month.toString().padLeft(2, '0')}/${_selectedDate!.year}",
                                style: TextStyle(
                                  color: _selectedDate == null ? AppTheme.textSecondary : AppTheme.textPrimary,
                                  fontSize: 15,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                      const SizedBox(height: 16),
                      // Giới tính Dropdown
                      DropdownButtonFormField<int>(
                        decoration: InputDecoration(
                          labelText: "Giới Tính",
                          labelStyle: const TextStyle(color: AppTheme.textSecondary, fontSize: 14),
                          prefixIcon: const Icon(Icons.wc, color: AppTheme.primary, size: 22),
                          filled: true,
                          fillColor: Colors.white.withValues(alpha: 0.05),
                          border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
                          enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: Colors.white10)),
                          focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: AppTheme.primary, width: 1.5)),
                        ),
                        dropdownColor: AppTheme.surfaceLight,
                        initialValue: _selectedGender,
                        style: const TextStyle(color: AppTheme.textPrimary, fontSize: 15),
                        items: const [
                          DropdownMenuItem(value: 1, child: Text("Nam")),
                          DropdownMenuItem(value: 0, child: Text("Nữ")),
                        ],
                        onChanged: (val) => setState(() => _selectedGender = val),
                      ),
                    ],
                  ),
                ).animate().fadeIn(duration: 400.ms).slideY(begin: 0.1, end: 0),

                const SizedBox(height: 24),
                // Nút Tiếp tục (chỉ hiển thị ở bước 0)
                if (_currentStep == 0)
                  SizedBox(
                    width: double.infinity,
                    child: NeuButton(
                      isPrimary: true,
                      onPressed: () {
                        if (_mssvCtrl.text.isEmpty || _nameCtrl.text.isEmpty) {
                          ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(content: Text("Vui lòng nhập đủ MSSV và Tên!")));
                          return;
                        }
                        if (_selectedLopId == null) {
                          ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(content: Text("Vui lòng chọn lớp học!")));
                          return;
                        }
                        setState(() => _currentStep = 1);
                      },
                      child: const Center(child: Text("Tiếp tục", style: TextStyle(fontWeight: FontWeight.bold))),
                    ),
                  ),
                ],

                if (_currentStep == 1) ...[
                  // Camera section header
                Row(
                  children: [
                    const Icon(Icons.camera_front,
                        color: AppTheme.primary, size: 20),
                    const SizedBox(width: 8),
                    const Text("Camera Khuôn Mặt",
                        style: TextStyle(
                            color: AppTheme.textPrimary,
                            fontSize: 16,
                            fontWeight: FontWeight.bold)),
                    const Spacer(),
                    if (_capturedImages.isNotEmpty)
                      GestureDetector(
                        onTap: _isRegistering
                            ? null
                            : () => setState(() => _capturedImages.clear()),
                        child: Container(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 10, vertical: 4),
                          decoration: BoxDecoration(
                            color: Colors.redAccent.withValues(alpha: 0.1),
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(
                                color: Colors.redAccent.withValues(alpha: 0.3)),
                          ),
                          child: const Text("Xóa tất cả",
                              style: TextStyle(
                                  color: Colors.redAccent, fontSize: 12)),
                        ),
                      ),
                  ],
                ).animate().fadeIn(delay: 200.ms),
                const SizedBox(height: 16),

                // Camera preview
                Center(
                  child: Container(
                    height: 340,
                    width: 280,
                    decoration: BoxDecoration(
                      color: AppTheme.surfaceLight,
                      borderRadius: BorderRadius.circular(24),
                      border: Border.all(
                        color: _capturedImages.length >= _maxPhotos
                            ? Colors.greenAccent.withValues(alpha: 0.5)
                            : AppTheme.primary.withValues(alpha: 0.5),
                        width: 2,
                      ),
                      boxShadow: [
                        BoxShadow(
                            color: _capturedImages.length >= _maxPhotos
                                ? Colors.greenAccent.withValues(alpha: 0.1)
                                : AppTheme.primary.withValues(alpha: 0.15),
                            blurRadius: 20,
                            spreadRadius: 2),
                      ],
                    ),
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(22),
                      child: _isCameraReady
                          ? Stack(
                              children: [
                                Positioned.fill(
                                    child: FittedBox(
                                      fit: BoxFit.cover,
                                      child: SizedBox(
                                        width: _controller!.value.previewSize?.height ?? 1,
                                        height: _controller!.value.previewSize?.width ?? 1,
                                        child: CameraPreview(_controller!),
                                      ),
                                    )),
                                Positioned.fill(
                                    child: CustomPaint(
                                        painter: OvalOverlayPainter())),
                                Positioned(
                                  bottom: 16,
                                  left: 0,
                                  right: 0,
                                  child: Center(
                                    child: Container(
                                      padding: const EdgeInsets.symmetric(
                                          horizontal: 16, vertical: 8),
                                      decoration: BoxDecoration(
                                        color: Colors.black.withValues(alpha: 0.7),
                                        borderRadius: BorderRadius.circular(20),
                                        border: Border.all(
                                            color: AppTheme.secondary
                                                .withValues(alpha: 0.5)),
                                      ),
                                      child: Text(
                                        _currentPoseGuide,
                                        style: const TextStyle(
                                            color: Colors.white,
                                            fontSize: 13,
                                            fontWeight: FontWeight.w600),
                                      ),
                                    ),
                                  ),
                                ),
                              ],
                            )
                          : const Center(
                              child: CircularProgressIndicator(
                                  color: AppTheme.primary)),
                    ),
                  ),
                )
                    .animate()
                    .fadeIn(delay: 300.ms)
                    .scale(begin: const Offset(0.9, 0.9)),

                const SizedBox(height: 20),

                // Thumbnail list
                // Thumbnail list (Dùng SizedBox cố định chiều cao để không đẩy nút chụp xuống)
                SizedBox(
                  height: 120,
                  child: _capturedImages.isNotEmpty ? Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text("Ảnh đã chụp",
                          style: TextStyle(
                              color: AppTheme.textSecondary,
                              fontSize: 14,
                              fontWeight: FontWeight.w500)),
                      const SizedBox(height: 12),
                      SizedBox(
                        height: 72,
                        child: ListView.builder(
                          scrollDirection: Axis.horizontal,
                          itemCount: _capturedImages.length,
                          itemBuilder: (context, index) {
                            return Padding(
                              padding: const EdgeInsets.only(right: 12),
                              child: Stack(
                                children: [
                                  Container(
                                    width: 64,
                                    height: 64,
                                    margin: const EdgeInsets.only(top: 6, right: 6),
                                    decoration: BoxDecoration(
                                      borderRadius: BorderRadius.circular(16),
                                      border: Border.all(
                                          color: AppTheme.primary.withValues(alpha: 0.8),
                                          width: 2),
                                      image: DecorationImage(
                                          image: MemoryImage(
                                              base64Decode(_capturedImages[index])),
                                          fit: BoxFit.cover),
                                      boxShadow: [
                                        BoxShadow(
                                            color: Colors.black.withValues(alpha: 0.3),
                                            blurRadius: 8,
                                            offset: const Offset(0, 4))
                                      ],
                                    ),
                                  ),
                                  Positioned(
                                    right: 0,
                                    top: 0,
                                    child: GestureDetector(
                                      onTap: () => setState(
                                          () => _capturedImages.removeAt(index)),
                                      child: Container(
                                        padding: const EdgeInsets.all(4),
                                        decoration: BoxDecoration(
                                          color: Colors.redAccent,
                                          shape: BoxShape.circle,
                                          border: Border.all(
                                              color: AppTheme.background, width: 2),
                                        ),
                                        child: const Icon(Icons.close,
                                            color: Colors.white, size: 12),
                                      ),
                                    ),
                                  ),
                                ],
                              ).animate().scale(begin: const Offset(0.5, 0.5)),
                            );
                          },
                        ),
                      ),
                    ],
                  ) : const SizedBox.shrink(),
                ),
                const SizedBox(height: 16),

                // Hướng dẫn
                NeuContainer(
                  padding: const EdgeInsets.all(16),
                  borderRadius: 16,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Icon(Icons.lightbulb_outline,
                              color: AppTheme.secondary.withValues(alpha: 0.8),
                              size: 24),
                          const SizedBox(width: 12),
                          const Text(
                            "Hướng dẫn chụp ảnh",
                            style: TextStyle(
                                color: AppTheme.textPrimary,
                                fontSize: 15,
                                fontWeight: FontWeight.bold),
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      const Text(
                        "• Tối thiểu 5 ảnh, khuyến nghị 15-20 ảnh\n"
                        "• Chụp nhiều góc: thẳng, trái, phải, lên, xuống\n"
                        "• Chụp cả biểu cảm: cười, nghiêm túc\n"
                        "• Chụp ở nhiều điều kiện sáng khác nhau\n"
                        "• Càng nhiều ảnh → AI nhận diện càng chính xác!",
                        style: TextStyle(
                            color: AppTheme.textSecondary,
                            fontSize: 13,
                            height: 1.6),
                      ),
                      const SizedBox(height: 10),
                      // Progress bar
                      ClipRRect(
                        borderRadius: BorderRadius.circular(4),
                        child: LinearProgressIndicator(
                          value: _capturedImages.length / _maxPhotos,
                          backgroundColor: Colors.white.withValues(alpha: 0.1),
                          valueColor: AlwaysStoppedAnimation<Color>(
                            _capturedImages.length >= _minPhotos
                                ? AppTheme.success
                                : AppTheme.secondary,
                          ),
                          minHeight: 6,
                        ),
                      ),
                      const SizedBox(height: 6),
                      Text(
                        _capturedImages.length < _minPhotos
                            ? 'Cần thêm ${_minPhotos - _capturedImages.length} ảnh nữa'
                            : _capturedImages.length < _maxPhotos
                                ? 'Đủ điều kiện! Chụp thêm ${_maxPhotos - _capturedImages.length} ảnh nữa để tăng độ chính xác'
                                : 'Đã đạt tối đa $_maxPhotos ảnh ✓',
                        style: TextStyle(
                          color: _capturedImages.length >= _minPhotos
                              ? AppTheme.success
                              : AppTheme.textMuted,
                          fontSize: 12,
                          fontStyle: FontStyle.italic,
                        ),
                      ),
                    ],
                  ),
                ).animate().fadeIn(delay: 400.ms),
                const SizedBox(height: 24),

                // Nút hành động
                // Nút chụp ảnh (hiển thị khi chưa đạt tối đa)
                if (_capturedImages.length < _maxPhotos)
                  SizedBox(
                    width: double.infinity,
                    height: 56,
                    child: ElevatedButton.icon(
                      onPressed: _takeSinglePicture,
                      icon: const Icon(Icons.camera_alt,
                          color: Colors.white, size: 22),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppTheme.surfaceLight,
                        shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(16),
                            side: const BorderSide(
                                color: AppTheme.primary, width: 1)),
                        elevation: 0,
                      ),
                      label: Text(
                          "Chụp ảnh (${_capturedImages.length}/$_maxPhotos)",
                          style: const TextStyle(
                              color: AppTheme.primary,
                              fontSize: 16,
                              fontWeight: FontWeight.bold)),
                    ),
                  ).animate().fadeIn(delay: 500.ms),

                // Nút gửi đăng ký (hiển thị khi đã đủ tối thiểu)
                if (_capturedImages.length >= _minPhotos) ...[
                  const SizedBox(height: 12),
                  SizedBox(
                    width: double.infinity,
                    height: 56,
                    child: Container(
                      decoration: BoxDecoration(
                          gradient: const LinearGradient(
                              colors: [Color(0xFF10B981), Color(0xFF059669)]),
                          borderRadius: BorderRadius.circular(16),
                          boxShadow: [
                            BoxShadow(
                                color: const Color(0xFF10B981).withValues(alpha: 0.4),
                                blurRadius: 12,
                                offset: const Offset(0, 6)),
                          ]),
                      child: ElevatedButton.icon(
                        onPressed: _isRegistering ? null : _submitRegistration,
                        icon: _isRegistering
                            ? const SizedBox(
                                width: 20,
                                height: 20,
                                child: CircularProgressIndicator(
                                    color: Colors.white, strokeWidth: 2))
                            : const Icon(Icons.cloud_upload,
                                color: Colors.white, size: 22),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.transparent,
                          shadowColor: Colors.transparent,
                          shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(16)),
                        ),
                        label: Text(
                          _isRegistering
                              ? "Đang gửi ${_capturedImages.length} ảnh..."
                              : "Gửi Đăng Ký (${_capturedImages.length} ảnh)",
                          style: const TextStyle(
                              color: Colors.white,
                              fontSize: 16,
                              fontWeight: FontWeight.bold),
                        ),
                      ),
                    ),
                  ).animate().fadeIn(),
                ],
                ], // End if _currentStep == 1

                const SizedBox(height: 40),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class OvalOverlayPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.black.withValues(alpha: 0.6)
      ..style = PaintingStyle.fill;

    final ovalRect = Rect.fromCenter(
      center: Offset(size.width / 2, size.height / 2 - 15),
      width: size.width * 0.8,
      height: size.height * 0.75,
    );

    final outerRect = Rect.fromLTWH(0, 0, size.width, size.height);
    final path = Path()
      ..addRect(outerRect)
      ..addOval(ovalRect)
      ..fillType = PathFillType.evenOdd;

    canvas.drawPath(path, paint);

    final borderPaint = Paint()
      ..color = AppTheme.primary.withValues(alpha: 0.8)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.0;
    canvas.drawOval(ovalRect, borderPaint);

    // Thêm các điểm góc nhỏ ngắm bắn
    final dashPaint = Paint()
      ..color = AppTheme.secondary
      ..style = PaintingStyle.stroke
      ..strokeWidth = 3.0;

    // Vẽ 4 góc định vị
    const double length = 15;
    canvas.drawLine(Offset(ovalRect.left, ovalRect.top + length),
        Offset(ovalRect.left, ovalRect.top), dashPaint);
    canvas.drawLine(Offset(ovalRect.left, ovalRect.top),
        Offset(ovalRect.left + length, ovalRect.top), dashPaint);

    canvas.drawLine(Offset(ovalRect.right - length, ovalRect.top),
        Offset(ovalRect.right, ovalRect.top), dashPaint);
    canvas.drawLine(Offset(ovalRect.right, ovalRect.top),
        Offset(ovalRect.right, ovalRect.top + length), dashPaint);

    canvas.drawLine(Offset(ovalRect.left, ovalRect.bottom - length),
        Offset(ovalRect.left, ovalRect.bottom), dashPaint);
    canvas.drawLine(Offset(ovalRect.left, ovalRect.bottom),
        Offset(ovalRect.left + length, ovalRect.bottom), dashPaint);

    canvas.drawLine(Offset(ovalRect.right - length, ovalRect.bottom),
        Offset(ovalRect.right, ovalRect.bottom), dashPaint);
    canvas.drawLine(Offset(ovalRect.right, ovalRect.bottom),
        Offset(ovalRect.right, ovalRect.bottom - length), dashPaint);
  }

  @override
  bool shouldRepaint(CustomPainter oldDelegate) => false;
}
