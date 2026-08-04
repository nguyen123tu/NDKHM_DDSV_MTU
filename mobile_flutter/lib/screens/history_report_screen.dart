import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../services/export_service.dart';
import '../theme/app_theme.dart';
import '../widgets/neu_container.dart';
import '../widgets/neu_button.dart';

class HistoryReportScreen extends StatefulWidget {
  const HistoryReportScreen({super.key});

  @override
  _HistoryReportScreenState createState() => _HistoryReportScreenState();
}

class _HistoryReportScreenState extends State<HistoryReportScreen> {
  final ApiService _apiService = ApiService();

  List<dynamic> _classes = [];
  int? _selectedLopId;
  DateTime? _selectedDate;
  int? _selectedMonth;
  final int _selectedYear = DateTime.now().year;

  List<dynamic> _history = [];
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _loadClasses();
  }

  Future<void> _loadClasses() async {
    try {
      final classes = await _apiService.getClasses();
      setState(() => _classes = classes);
    } catch (e) {
      debugPrint("Lỗi tải lớp: $e");
    }
  }

  Future<void> _fetchHistory() async {
    setState(() => _isLoading = true);
    try {
      String? dateStr;
      if (_selectedDate != null) {
        dateStr =
            "${_selectedDate!.year}-${_selectedDate!.month.toString().padLeft(2, '0')}-${_selectedDate!.day.toString().padLeft(2, '0')}";
      }

      final response = await _apiService.getHistory(
        limit: 500,
        lopId: _selectedLopId,
        date: dateStr,
        month: _selectedMonth,
        year: _selectedYear,
      );

      if (response['success'] == true) {
        setState(() {
          _history = response['data'] ?? [];
          _isLoading = false;
        });
      } else {
        setState(() => _isLoading = false);
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
                content: Text(response['message'] ?? 'Không thể tải dữ liệu'),
                backgroundColor: Colors.orange),
          );
        }
      }
    } catch (e) {
      setState(() => _isLoading = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
              content: Text("Mất kết nối server. Vui lòng thử lại."),
              backgroundColor: Colors.red),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      appBar: AppBar(
        title: const Text("Báo cáo điểm danh",
            style: TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: Theme.of(context).scaffoldBackgroundColor,
        foregroundColor:
            Theme.of(context).textTheme.bodyLarge?.color ?? Colors.black,
        elevation: 0.0,
        actions: [
          if (_history.isNotEmpty)
            IconButton(
              icon: const Icon(Icons.file_download_outlined,
                  color: Color(0xFF10B981)),
              onPressed: () => ExportService.exportAttendanceToExcel(_history),
            )
        ],
      ),
      body: Column(
        children: [
          // Filter Section
          NeuContainer(
            padding: const EdgeInsets.all(16),
            child: Column(
              children: [
                Row(
                  children: [
                    Expanded(
                      child: DropdownButtonFormField<int>(
                        decoration: const InputDecoration(
                            labelText: "Lớp học", border: OutlineInputBorder()),
                        initialValue: _selectedLopId,
                        items: [
                          const DropdownMenuItem(
                              value: null, child: Text("Tất cả lớp")),
                          ..._classes.map((c) => DropdownMenuItem(
                              value: c['id'], child: Text(c['ten_lop'])))
                        ],
                        onChanged: (val) =>
                            setState(() => _selectedLopId = val),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    Expanded(
                      child: NeuButton(
                        onPressed: () async {
                          final date = await showDatePicker(
                            context: context,
                            initialDate: DateTime.now(),
                            firstDate: DateTime(2020),
                            lastDate: DateTime.now(),
                          );
                          if (date != null) {
                            setState(() {
                              _selectedDate = date;
                              _selectedMonth = null;
                            });
                          }
                        },
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            const Icon(Icons.calendar_today, size: 16),
                            const SizedBox(width: 8),
                            Text(_selectedDate == null
                                ? "Chọn ngày"
                                : "${_selectedDate!.day}/${_selectedDate!.month}/${_selectedDate!.year}"),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: DropdownButtonFormField<int>(
                        decoration: const InputDecoration(
                            labelText: "Tháng", border: OutlineInputBorder()),
                        initialValue: _selectedMonth,
                        items: [
                          const DropdownMenuItem(
                              value: null, child: Text("Chọn tháng")),
                          ...List.generate(
                              12,
                              (i) => DropdownMenuItem(
                                  value: i + 1, child: Text("Tháng ${i + 1}")))
                        ],
                        onChanged: (val) => setState(() {
                          _selectedMonth = val;
                          if (val != null) _selectedDate = null;
                        }),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                SizedBox(
                  width: double.infinity,
                  child: NeuButton(
                    isPrimary: true,
                    onPressed: _fetchHistory,
                    child: const Center(
                      child: Text("LỌC DỮ LIỆU",
                          style: TextStyle(
                              color: Colors.white,
                              fontWeight: FontWeight.bold)),
                    ),
                  ),
                ),
              ],
            ),
          ),

          // List Section
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : _history.isEmpty
                    ? const Center(child: Text("Không có dữ liệu khớp bộ lọc"))
                    : ListView.builder(
                        padding: const EdgeInsets.all(12),
                        itemCount: _history.length,
                        itemBuilder: (context, index) {
                          final item = _history[index];
                          return NeuContainer(
                            margin: const EdgeInsets.only(bottom: 12),
                            borderRadius: 12,
                            child: ListTile(
                              leading: const CircleAvatar(
                                  backgroundColor: AppTheme.secondary,
                                  child:
                                      Icon(Icons.person, color: Colors.white)),
                              title: Text(item['ho_ten'],
                                  style: const TextStyle(
                                      fontWeight: FontWeight.bold)),
                              subtitle:
                                  Text("${item['mssv']} • ${item['ma_lop']}"),
                              trailing: Column(
                                mainAxisAlignment: MainAxisAlignment.center,
                                crossAxisAlignment: CrossAxisAlignment.end,
                                children: [
                                  Row(
                                    mainAxisSize: MainAxisSize.min,
                                    children: [
                                      const Icon(Icons.login,
                                          size: 12, color: Colors.green),
                                      const SizedBox(width: 4),
                                      Text(
                                          item['thoi_gian'] != null
                                              ? item['thoi_gian']
                                                  .toString()
                                                  .split(' ')
                                                  .last
                                              : '--:--',
                                          style: const TextStyle(
                                              fontWeight: FontWeight.bold,
                                              color: Colors.green)),
                                    ],
                                  ),
                                  const SizedBox(height: 4),
                                  Row(
                                    mainAxisSize: MainAxisSize.min,
                                    children: [
                                      const Icon(Icons.logout,
                                          size: 12, color: Colors.orange),
                                      const SizedBox(width: 4),
                                      Text(
                                          item['gio_ra'] != null
                                              ? item['gio_ra']
                                                  .toString()
                                                  .split(' ')
                                                  .last
                                              : '--:--',
                                          style: const TextStyle(
                                              fontWeight: FontWeight.bold,
                                              color: Colors.orange)),
                                    ],
                                  ),
                                ],
                              ),
                            ),
                          );
                        },
                      ),
          )
        ],
      ),
    );
  }
}
