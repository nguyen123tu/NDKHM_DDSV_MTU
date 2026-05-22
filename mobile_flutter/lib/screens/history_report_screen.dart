
import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../services/export_service.dart';
// import '../models/attendance_model.dart'; // Bỏ qua vì dùng dynamic

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
  int _selectedYear = DateTime.now().year;
  
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
      print("Lỗi tải lớp: $e");
    }
  }

  Future<void> _fetchHistory() async {
    setState(() => _isLoading = true);
    try {
      String? dateStr;
      if (_selectedDate != null) {
        dateStr = "${_selectedDate!.year}-${_selectedDate!.month.toString().padLeft(2, '0')}-${_selectedDate!.day.toString().padLeft(2, '0')}";
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
          _history = response['data'];
          _isLoading = false;
        });
      }
    } catch (e) {
      setState(() => _isLoading = false);
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Lỗi: $e")));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        title: const Text("Báo cáo điểm danh", style: TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: Colors.white,
        foregroundColor: const Color(0xFF1E293B),
        elevation: 0.5,
        actions: [
          if (_history.isNotEmpty)
            IconButton(
              icon: const Icon(Icons.file_download_outlined, color: Color(0xFF10B981)),
              onPressed: () => ExportService.exportAttendanceToExcel(_history),
            )
        ],
      ),
      body: Column(
        children: [
          // Filter Section
          Container(
            padding: const EdgeInsets.all(16),
            color: Colors.white,
            child: Column(
              children: [
                Row(
                  children: [
                    Expanded(
                      child: DropdownButtonFormField<int>(
                        decoration: const InputDecoration(labelText: "Lớp học", border: OutlineInputBorder()),
                        value: _selectedLopId,
                        items: [
                          const DropdownMenuItem(value: null, child: Text("Tất cả lớp")),
                          ..._classes.map((c) => DropdownMenuItem(value: c['id'], child: Text(c['ten_lop'])))
                        ],
                        onChanged: (val) => setState(() => _selectedLopId = val),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    Expanded(
                      child: OutlinedButton.icon(
                        icon: const Icon(Icons.calendar_today, size: 16),
                        label: Text(_selectedDate == null ? "Chọn ngày" : "${_selectedDate!.day}/${_selectedDate!.month}/${_selectedDate!.year}"),
                        onPressed: () async {
                          final date = await showDatePicker(
                            context: context,
                            initialDate: DateTime.now(),
                            firstDate: DateTime(2020),
                            lastDate: DateTime.now(),
                          );
                          if (date != null) setState(() { _selectedDate = date; _selectedMonth = null; });
                        },
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: DropdownButtonFormField<int>(
                        decoration: const InputDecoration(labelText: "Tháng", border: OutlineInputBorder()),
                        value: _selectedMonth,
                        items: [
                          const DropdownMenuItem(value: null, child: Text("Chọn tháng")),
                          ...List.generate(12, (i) => DropdownMenuItem(value: i + 1, child: Text("Tháng ${i + 1}")))
                        ],
                        onChanged: (val) => setState(() { _selectedMonth = val; if(val != null) _selectedDate = null; }),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                SizedBox(
                  width: double.infinity,
                  height: 45,
                  child: ElevatedButton(
                    onPressed: _fetchHistory,
                    style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF1E293B)),
                    child: const Text("LỌC DỮ LIỆU", style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
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
                      return Card(
                        margin: const EdgeInsets.only(bottom: 8),
                        child: ListTile(
                          leading: const CircleAvatar(backgroundColor: Color(0xFFEDF2F9), child: Icon(Icons.person, color: Color(0xFF1E293B))),
                          title: Text(item['ho_ten'], style: const TextStyle(fontWeight: FontWeight.bold)),
                          subtitle: Text("${item['mssv']} • ${item['ma_lop']}"),
                          trailing: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            crossAxisAlignment: CrossAxisAlignment.end,
                            children: [
                              Text(item['thoi_gian'].toString().split(' ')[0], style: const TextStyle(fontSize: 12)),
                              Text(item['thoi_gian'].toString().split(' ')[1], style: const TextStyle(fontWeight: FontWeight.bold)),
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
