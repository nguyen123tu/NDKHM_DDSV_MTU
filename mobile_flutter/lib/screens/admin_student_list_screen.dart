import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../services/api_service.dart';
import '../theme/app_theme.dart';
import 'admin_student_edit_screen.dart';
import '../widgets/neu_container.dart';

class AdminStudentListScreen extends StatefulWidget {
  const AdminStudentListScreen({super.key});

  @override
  State<AdminStudentListScreen> createState() => _AdminStudentListScreenState();
}

class _AdminStudentListScreenState extends State<AdminStudentListScreen> {
  final ApiService _api = ApiService();
  bool _isLoading = false;
  List<dynamic> _students = [];
  final TextEditingController _searchController = TextEditingController();
  Timer? _debounce;

  @override
  void initState() {
    super.initState();
    _fetchStudents();
  }

  @override
  void dispose() {
    _debounce?.cancel();
    _searchController.dispose();
    super.dispose();
  }

  void _onSearchChanged(String query) {
    if (_debounce?.isActive ?? false) _debounce!.cancel();
    _debounce = Timer(const Duration(milliseconds: 500), () {
      _fetchStudents(query: query);
    });
  }

  Future<void> _fetchStudents({String query = ''}) async {
    setState(() => _isLoading = true);
    final res = await _api.getAdminStudents(query: query);
    if (mounted) {
      setState(() {
        _isLoading = false;
        if (res['success'] == true) {
          _students = res['data'] ?? [];
        }
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      appBar: AppBar(
        title: const Text('Quản Lý Sinh Viên',
            style: TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: Colors.transparent,
        foregroundColor: AppTheme.textPrimary,
        elevation: 0,
      ),
      body: Stack(
        children: [
          Container(color: Theme.of(context).scaffoldBackgroundColor),
          Column(
            children: [
              // Search Bar
              Padding(
                padding: const EdgeInsets.all(20),
                child: NeuContainer(
                  borderRadius: 16,
                  child: TextField(
                    controller: _searchController,
                    style: const TextStyle(color: AppTheme.textPrimary),
                    onChanged: _onSearchChanged,
                    onSubmitted: (value) => _fetchStudents(query: value),
                    decoration: InputDecoration(
                      hintText: "Tìm theo tên hoặc MSSV...",
                      hintStyle: const TextStyle(color: AppTheme.textMuted),
                      prefixIcon:
                          const Icon(Icons.search, color: AppTheme.secondary),
                      suffixIcon: IconButton(
                        icon:
                            const Icon(Icons.clear, color: AppTheme.textMuted),
                        onPressed: () {
                          _searchController.clear();
                          _fetchStudents();
                        },
                      ),
                      border: InputBorder.none,
                      contentPadding: const EdgeInsets.symmetric(vertical: 16),
                    ),
                  ),
                ),
              ).animate().fadeIn(duration: 300.ms).slideY(begin: -0.1),

              // Student List
              Expanded(
                child: _isLoading
                    ? const Center(
                        child: CircularProgressIndicator(
                            color: AppTheme.secondary))
                    : _students.isEmpty
                        ? Center(
                            child: Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Icon(Icons.group_off,
                                    size: 64,
                                    color: Colors.white.withValues(alpha: 0.1)),
                                const SizedBox(height: 16),
                                const Text("Không tìm thấy sinh viên nào",
                                    style:
                                        TextStyle(color: AppTheme.textMuted)),
                              ],
                            ),
                          )
                        : RefreshIndicator(
                            onRefresh: () =>
                                _fetchStudents(query: _searchController.text),
                            color: AppTheme.secondary,
                            backgroundColor: AppTheme.surfaceLight,
                            child: ListView.builder(
                              padding: const EdgeInsets.symmetric(
                                  horizontal: 20, vertical: 8),
                              itemCount: _students.length,
                              itemBuilder: (context, index) {
                                final s = _students[index];
                                final bool hasFace = (s['trang_thai'] ?? 0) ==
                                    1; // Assuming 1 = has face

                                return NeuContainer(
                                  margin: const EdgeInsets.only(bottom: 12),
                                  borderRadius: 16,
                                  child: ListTile(
                                    contentPadding: const EdgeInsets.symmetric(
                                        horizontal: 16, vertical: 8),
                                    leading: CircleAvatar(
                                      backgroundColor:
                                          AppTheme.primary.withValues(alpha: 0.2),
                                      child: const Icon(Icons.person,
                                          color: AppTheme.secondary),
                                    ),
                                    title: Text(s['ho_ten'] ?? '',
                                        style: const TextStyle(
                                            fontWeight: FontWeight.bold,
                                            color: AppTheme.textPrimary)),
                                    subtitle: Padding(
                                      padding: const EdgeInsets.only(top: 4),
                                      child: Row(
                                        children: [
                                          Text(s['mssv'] ?? '',
                                              style: const TextStyle(
                                                  color: AppTheme.textSecondary,
                                                  fontSize: 13)),
                                          const Text(' • ',
                                              style: TextStyle(
                                                  color: AppTheme.textMuted)),
                                          Text(s['ma_lop'] ?? '',
                                              style: const TextStyle(
                                                  color: AppTheme.textSecondary,
                                                  fontSize: 13)),
                                        ],
                                      ),
                                    ),
                                    trailing: const Icon(Icons.edit_square,
                                        color: AppTheme.textMuted, size: 20),
                                    onTap: () async {
                                      final result = await Navigator.push(
                                        context,
                                        MaterialPageRoute(
                                          builder: (_) =>
                                              AdminStudentEditScreen(
                                                  student: s),
                                        ),
                                      );
                                      if (result == true) {
                                        _fetchStudents(
                                            query: _searchController.text);
                                      }
                                    },
                                  ),
                                )
                                    .animate()
                                    .fadeIn(
                                        delay:
                                            Duration(milliseconds: 50 * index))
                                    .slideX(begin: 0.1);
                              },
                            ),
                          ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
