import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../widgets/api_image.dart';

class FaceApprovalScreen extends StatefulWidget {
  const FaceApprovalScreen({super.key});

  @override
  _FaceApprovalScreenState createState() => _FaceApprovalScreenState();
}

class _FaceApprovalScreenState extends State<FaceApprovalScreen> {
  final ApiService _apiService = ApiService();
  List<dynamic> _pendingList = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadPending();
  }

  Future<void> _loadPending() async {
    setState(() => _isLoading = true);
    try {
      final res = await _apiService.getPendingFaces();
      if (res['success'] == true) {
        setState(() => _pendingList = res['data']);
      }
    } catch (e) {
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text("Lỗi: $e")));
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _handleAction(int id, int status) async {
    try {
      final res = await _apiService.approveFace(id, status);
      if (res['success'] == true) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(res['message'])));
        _loadPending();
      }
    } catch (e) {
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text("Lỗi: $e")));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        title: const Text("Phê duyệt khuôn mặt",
            style: TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: Colors.white,
        foregroundColor: const Color(0xFF1E293B),
        elevation: 0.5,
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _pendingList.isEmpty
              ? const Center(child: Text("Không có yêu cầu chờ duyệt"))
              : ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: _pendingList.length,
                  itemBuilder: (context, index) {
                    final item = _pendingList[index];
                    return Card(
                      shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(15)),
                      margin: const EdgeInsets.only(bottom: 16),
                      child: Padding(
                        padding: const EdgeInsets.all(12),
                        child: Column(
                          children: [
                            ListTile(
                              leading: ClipRRect(
                                borderRadius: BorderRadius.circular(30),
                                child: SizedBox(
                                  width: 60,
                                  height: 60,
                                  child: ApiImage(
                                    path: item['avatar']
                                            .contains('uploads/avatars')
                                        ? "static/${item['avatar']}"
                                        : "database/${item['avatar']}",
                                    fit: BoxFit.cover,
                                    errorWidget: const Icon(Icons.person,
                                        size: 30, color: Colors.grey),
                                  ),
                                ),
                              ),
                              title: Text(item['ho_ten'],
                                  style: const TextStyle(
                                      fontWeight: FontWeight.bold)),
                              subtitle:
                                  Text("${item['mssv']} • ${item['ma_lop']}"),
                            ),
                            const Divider(),
                            Row(
                              mainAxisAlignment: MainAxisAlignment.end,
                              children: [
                                TextButton.icon(
                                  onPressed: () => _handleAction(item['id'], 3),
                                  icon: const Icon(Icons.close,
                                      color: Colors.red),
                                  label: const Text("Từ chối",
                                      style: TextStyle(color: Colors.red)),
                                ),
                                const SizedBox(width: 8),
                                ElevatedButton.icon(
                                  onPressed: () => _handleAction(item['id'], 2),
                                  icon: const Icon(Icons.check,
                                      color: Colors.white),
                                  label: const Text("Phê duyệt",
                                      style: TextStyle(color: Colors.white)),
                                  style: ElevatedButton.styleFrom(
                                      backgroundColor: Colors.green),
                                ),
                              ],
                            )
                          ],
                        ),
                      ),
                    );
                  },
                ),
    );
  }
}
