import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import '../services/api_service.dart';

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});

  @override
  _RegisterScreenState createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _mssvCtrl = TextEditingController();
  final _nameCtrl = TextEditingController();

  List<dynamic> _classes = [];
  int? _selectedLopId;

  CameraController? _controller;
  List<CameraDescription>? _cameras;
  bool _isCameraReady = false;
  bool _isRegistering = false;
  List<String> _capturedImages = [];

  final ApiService _apiService = ApiService();

  @override
  void initState() {
    super.initState();
    _initCamera();
    _loadClasses();
  }

  Future<void> _loadClasses() async {
    try {
      final classes = await _apiService.getClasses();
      if (mounted) {
        setState(() {
          _classes = classes;
          if (_classes.isNotEmpty) {
            _selectedLopId = _classes.first['id'];
          }
        });
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Lỗi tải danh sách lớp: $e")));
      }
    }
  }

  Future<void> _initCamera() async {
    _cameras = await availableCameras();
    if (_cameras != null && _cameras!.isNotEmpty) {
      final frontCamera = _cameras!.firstWhere(
        (c) => c.lensDirection == CameraLensDirection.front,
        orElse: () => _cameras![0],
      );
      _controller = CameraController(frontCamera, ResolutionPreset.medium);
      await _controller!.initialize();
      if (!mounted) return;
      setState(() => _isCameraReady = true);
    }
  }

  @override
  void dispose() {
    _controller?.dispose();
    super.dispose();
  }

  Future<void> _takeSinglePicture() async {
    if (_controller == null || !_controller!.value.isInitialized) return;
    if (_capturedImages.length >= 5) return;
    try {
      final image = await _controller!.takePicture();
      final bytes = await image.readAsBytes();
      setState(() {
        _capturedImages.add(base64Encode(bytes));
      });
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Lỗi chụp ảnh: $e")));
      }
    }
  }

  Future<void> _submitRegistration() async {
    if (_mssvCtrl.text.isEmpty || _nameCtrl.text.isEmpty || _selectedLopId == null) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Vui lòng nhập đủ thông tin và chọn lớp học!")));
      return;
    }
    if (_capturedImages.length < 5) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Vui lòng chụp đủ 5 bức ảnh!")));
      return;
    }
    setState(() => _isRegistering = true);
    try {
      List<String> base64List = _capturedImages.map((b64) => "data:image/jpeg;base64,$b64").toList();
      final result = await _apiService.registerFace(_mssvCtrl.text.trim(), _nameCtrl.text.trim(), _selectedLopId!, base64List);
      if (!mounted) return;
      if (result['success'] == true) {
        showDialog(
          context: context,
          builder: (c) => AlertDialog(
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
            title: Row(children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(color: const Color(0xFF10B981).withOpacity(0.1), shape: BoxShape.circle),
                child: const Icon(Icons.check_circle, color: Color(0xFF10B981), size: 28),
              ),
              const SizedBox(width: 12),
              const Text("Thành công!", style: TextStyle(color: Color(0xFF2C3E50))),
            ]),
            content: Text(result['message'], style: const TextStyle(color: Color(0xFF6C757D))),
            actions: [
              TextButton(
                onPressed: () {
                  Navigator.pop(c);
                  Navigator.pop(context);
                },
                child: const Text("OK", style: TextStyle(color: Color(0xFF2E96EB))),
              )
            ],
          ),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("Lỗi: ${result['message']}"), backgroundColor: const Color(0xFFEF4444)),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("Lỗi phần cứng/mạng: $e"), backgroundColor: const Color(0xFFEF4444)),
        );
      }
    } finally {
      if (mounted) setState(() => _isRegistering = false);
    }
  }

  Widget _buildInputField({required TextEditingController controller, required String label, required IconData icon}) {
    return TextField(
      controller: controller,
      style: const TextStyle(color: Color(0xFF2C3E50)),
      decoration: InputDecoration(
        labelText: label,
        labelStyle: const TextStyle(color: Color(0xFF6C757D), fontSize: 14),
        prefixIcon: Icon(icon, color: const Color(0xFF2E96EB), size: 22),
        filled: true,
        fillColor: const Color(0xFFF8FAFC),
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
        enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: Color(0xFFEDF2F9))),
        focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: Color(0xFF2E96EB), width: 1.5)),
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        title: const Text("Đăng ký Khuôn mặt", style: TextStyle(fontWeight: FontWeight.bold, color: Colors.white, fontSize: 18)),
        backgroundColor: const Color(0xFF2E96EB),
        foregroundColor: Colors.white,
        elevation: 0,
        actions: [
          Container(
            margin: const EdgeInsets.only(right: 12),
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            decoration: BoxDecoration(
              color: _capturedImages.length == 5 ? Colors.white.withOpacity(0.25) : Colors.white.withOpacity(0.15),
              borderRadius: BorderRadius.circular(20),
            ),
            child: Center(
              child: Text(
                "${_capturedImages.length}/5 ảnh",
                style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 13),
              ),
            ),
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Form card
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: const Color(0xFFEDF2F9)),
                boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.03), blurRadius: 10, offset: const Offset(0, 4))],
              ),
              child: Column(
                children: [
                  _buildInputField(controller: _mssvCtrl, label: "Mã Sinh Viên (MSSV)", icon: Icons.badge),
                  const SizedBox(height: 14),
                  _buildInputField(controller: _nameCtrl, label: "Họ và Tên", icon: Icons.person),
                  const SizedBox(height: 14),
                  // Dropdown
                  if (_classes.isEmpty)
                    const Padding(
                      padding: EdgeInsets.all(16),
                      child: Center(child: CircularProgressIndicator(color: Color(0xFF2E96EB), strokeWidth: 2)),
                    )
                  else
                    DropdownButtonFormField<int>(
                      decoration: InputDecoration(
                        labelText: "Lớp Học",
                        labelStyle: const TextStyle(color: Color(0xFF6C757D), fontSize: 14),
                        prefixIcon: const Icon(Icons.school, color: Color(0xFF2E96EB), size: 22),
                        filled: true,
                        fillColor: const Color(0xFFF8FAFC),
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
                        enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: Color(0xFFEDF2F9))),
                        focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: Color(0xFF2E96EB), width: 1.5)),
                      ),
                      value: _selectedLopId,
                      style: const TextStyle(color: Color(0xFF2C3E50), fontSize: 15),
                      items: _classes.map<DropdownMenuItem<int>>((dynamic c) {
                        return DropdownMenuItem<int>(value: c['id'] as int, child: Text("${c['ten_lop']} (${c['ma_lop']})"));
                      }).toList(),
                      onChanged: (int? newValue) { setState(() { _selectedLopId = newValue; }); },
                    ),
                ],
              ),
            ),

            const SizedBox(height: 20),

            // Camera section
            Row(
              children: [
                const Icon(Icons.camera_front, color: Color(0xFF2E96EB), size: 20),
                const SizedBox(width: 8),
                const Text("Camera Khuôn Mặt", style: TextStyle(color: Color(0xFF2C3E50), fontSize: 15, fontWeight: FontWeight.w600)),
                const Spacer(),
                if (_capturedImages.isNotEmpty)
                  GestureDetector(
                    onTap: _isRegistering ? null : () => setState(() => _capturedImages.clear()),
                    child: const Text("Xóa tất cả", style: TextStyle(color: Color(0xFFEF4444), fontSize: 13)),
                  ),
              ],
            ),
            const SizedBox(height: 12),

            // Camera preview
            Center(
              child: Container(
                height: 320,
                width: 260,
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(
                    color: _capturedImages.length == 5 ? const Color(0xFF10B981) : const Color(0xFF2E96EB),
                    width: 2.5,
                  ),
                  boxShadow: [
                    BoxShadow(color: const Color(0xFF2E96EB).withOpacity(0.15), blurRadius: 20, spreadRadius: 2),
                  ],
                ),
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(18),
                  child: _isCameraReady
                      ? Stack(
                          children: [
                            Positioned.fill(child: CameraPreview(_controller!)),
                            Positioned.fill(child: CustomPaint(painter: OvalOverlayPainter())),
                            Positioned(
                              bottom: 12,
                              left: 0,
                              right: 0,
                              child: Center(
                                child: Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
                                  decoration: BoxDecoration(
                                    color: Colors.black.withOpacity(0.5),
                                    borderRadius: BorderRadius.circular(20),
                                  ),
                                  child: const Text("Đặt khuôn mặt vào khung", style: TextStyle(color: Colors.white, fontSize: 11)),
                                ),
                              ),
                            ),
                          ],
                        )
                      : Container(
                          color: const Color(0xFFEDF2F9),
                          child: const Center(child: CircularProgressIndicator(color: Color(0xFF2E96EB))),
                        ),
                ),
              ),
            ),

            const SizedBox(height: 16),

            // Thumbnail list
            if (_capturedImages.isNotEmpty) ...[
              const Text("Ảnh đã chụp", style: TextStyle(color: Color(0xFF6C757D), fontSize: 13, fontWeight: FontWeight.w500)),
              const SizedBox(height: 8),
              SizedBox(
                height: 80,
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
                              borderRadius: BorderRadius.circular(12),
                              border: Border.all(color: const Color(0xFF2E96EB), width: 2),
                              image: DecorationImage(image: MemoryImage(base64Decode(_capturedImages[index])), fit: BoxFit.cover),
                              boxShadow: [BoxShadow(color: const Color(0xFF2E96EB).withOpacity(0.2), blurRadius: 8, offset: const Offset(0, 3))],
                            ),
                          ),
                          Positioned(
                            right: 0,
                            top: 0,
                            child: GestureDetector(
                              onTap: () => setState(() => _capturedImages.removeAt(index)),
                              child: Container(
                                padding: const EdgeInsets.all(3),
                                decoration: const BoxDecoration(color: Color(0xFFEF4444), shape: BoxShape.circle),
                                child: const Icon(Icons.close, color: Colors.white, size: 12),
                              ),
                            ),
                          ),
                        ],
                      ),
                    );
                  },
                ),
              ),
              const SizedBox(height: 12),
            ],

            // Hướng dẫn
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: const Color(0xFF2E96EB).withOpacity(0.06),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: const Color(0xFF2E96EB).withOpacity(0.15)),
              ),
              child: Row(
                children: [
                  Icon(Icons.info_outline, color: const Color(0xFF2E96EB).withOpacity(0.7), size: 20),
                  const SizedBox(width: 10),
                  const Expanded(
                    child: Text(
                      "Chụp 5 ảnh ở các góc khác nhau: thẳng, trái, phải, ngước lên, cúi xuống.",
                      style: TextStyle(color: Color(0xFF6C757D), fontSize: 12.5, height: 1.4),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),

            // Nút hành động
            if (_capturedImages.length < 5)
              SizedBox(
                width: double.infinity,
                height: 50,
                child: ElevatedButton.icon(
                  onPressed: _takeSinglePicture,
                  icon: const Icon(Icons.camera_alt, color: Colors.white, size: 22),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF2E96EB),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    elevation: 0,
                  ),
                  label: Text("Chụp ảnh (${_capturedImages.length}/5)", style: const TextStyle(color: Colors.white, fontSize: 15, fontWeight: FontWeight.bold)),
                ),
              )
            else
              SizedBox(
                width: double.infinity,
                height: 50,
                child: ElevatedButton.icon(
                  onPressed: _isRegistering ? null : _submitRegistration,
                  icon: _isRegistering
                      ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                      : const Icon(Icons.cloud_upload, color: Colors.white, size: 22),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF10B981),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    elevation: 0,
                  ),
                  label: Text(
                    _isRegistering ? "Đang gửi..." : "Gửi Đăng Ký",
                    style: const TextStyle(color: Colors.white, fontSize: 15, fontWeight: FontWeight.bold),
                  ),
                ),
              ),
            const SizedBox(height: 30),
          ],
        ),
      ),
    );
  }
}

class OvalOverlayPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.black.withOpacity(0.45)
      ..style = PaintingStyle.fill;

    final ovalRect = Rect.fromCenter(
      center: Offset(size.width / 2, size.height / 2 - 10),
      width: size.width * 0.82,
      height: size.height * 0.78,
    );

    final outerRect = Rect.fromLTWH(0, 0, size.width, size.height);
    final path = Path()
      ..addRect(outerRect)
      ..addOval(ovalRect)
      ..fillType = PathFillType.evenOdd;

    canvas.drawPath(path, paint);

    final borderPaint = Paint()
      ..color = const Color(0xFF2E96EB)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.5;
    canvas.drawOval(ovalRect, borderPaint);
  }

  @override
  bool shouldRepaint(CustomPainter oldDelegate) => false;
}
