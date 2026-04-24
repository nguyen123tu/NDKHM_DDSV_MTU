
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

class DeviceSettingsScreen extends StatefulWidget {
  const DeviceSettingsScreen({super.key});

  @override
  _DeviceSettingsScreenState createState() => _DeviceSettingsScreenState();
}

class _DeviceSettingsScreenState extends State<DeviceSettingsScreen> {
  double _threshold = 0.45;
  bool _allowMask = true;
  bool _antiFake = false;
  bool _canAdjust = true;

  @override
  void initState() {
    super.initState();
    _loadSettings();
  }

  Future<void> _loadSettings() async {
    final prefs = await SharedPreferences.getInstance();
    setState(() {
      _threshold = prefs.getDouble('ai_threshold') ?? 0.45;
      _allowMask = prefs.getBool('allow_mask') ?? true;
      _antiFake = prefs.getBool('anti_fake') ?? false;
      _canAdjust = prefs.getBool('can_adjust_threshold') ?? true;
    });
  }

  Future<void> _saveSettings() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setDouble('ai_threshold', _threshold);
    await prefs.setBool('allow_mask', _allowMask);
    await prefs.setBool('anti_fake', _antiFake);
    await prefs.setBool('can_adjust_threshold', _canAdjust);
    
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Đã lưu cấu hình thiết bị")),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        title: const Text("Cấu hình thiết bị", style: TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: Colors.white,
        foregroundColor: const Color(0xFF1B3A5C),
        elevation: 0.5,
      ),
      body: SingleChildScrollView(
        child: Column(
          children: [
            const SizedBox(height: 30),
            // Gauge Section
            Center(
              child: Container(
                width: 250,
                height: 250,
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: Colors.white,
                  shape: BoxShape.circle,
                  boxShadow: [
                    BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 20, spreadRadius: 5),
                  ],
                ),
                child: Stack(
                  alignment: Alignment.center,
                  children: [
                    SizedBox(
                      width: 200,
                      height: 200,
                      child: CircularProgressIndicator(
                        value: _threshold,
                        strokeWidth: 15,
                        backgroundColor: const Color(0xFFEDF2F9),
                        color: const Color(0xFF1B3A5C),
                      ),
                    ),
                    Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Text(
                          "${(_threshold * 100).toInt()}%",
                          style: const TextStyle(fontSize: 40, fontWeight: FontWeight.bold, color: Color(0xFF1B3A5C)),
                        ),
                        const Text("Ngưỡng AI", style: TextStyle(color: Colors.grey, fontSize: 14)),
                      ],
                    ),
                  ],
                ),
              ),
            ),
            
            const SizedBox(height: 20),
            Slider(
              value: _threshold,
              min: 0.1,
              max: 0.9,
              divisions: 80,
              activeColor: const Color(0xFF1B3A5C),
              onChanged: _canAdjust ? (val) => setState(() => _threshold = val) : null,
            ),
            TextButton(
              onPressed: () => setState(() => _threshold = 0.45),
              child: const Text("Đặt lại mặc định", style: TextStyle(color: Color(0xFF2E96EB))),
            ),

            const SizedBox(height: 20),
            
            // Settings List
            Container(
              margin: const EdgeInsets.symmetric(horizontal: 20),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: const Color(0xFFEDF2F9)),
              ),
              child: Column(
                children: [
                  _buildToggleTile(
                    icon: Icons.edit_attributes,
                    title: "Cho phép điều chỉnh ngưỡng",
                    value: _canAdjust,
                    onChanged: (v) => setState(() => _canAdjust = v),
                  ),
                  const Divider(height: 1, indent: 60),
                  _buildToggleTile(
                    icon: Icons.face_retouching_natural,
                    title: "Cho phép mặt bị che",
                    value: _allowMask,
                    onChanged: (v) => setState(() => _allowMask = v),
                  ),
                  const Divider(height: 1, indent: 60),
                  _buildToggleTile(
                    icon: Icons.security,
                    title: "Chống Fake (Liveness)",
                    value: _antiFake,
                    onChanged: (v) => setState(() => _antiFake = v),
                  ),
                ],
              ),
            ),
            
            const SizedBox(height: 40),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: SizedBox(
                width: double.infinity,
                height: 50,
                child: ElevatedButton(
                  onPressed: _saveSettings,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF1B3A5C),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                  child: const Text("LƯU CẤU HÌNH", style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                ),
              ),
            ),
            const SizedBox(height: 20),
          ],
        ),
      ),
    );
  }

  Widget _buildToggleTile({required IconData icon, required String title, required bool value, required Function(bool) onChanged}) {
    return ListTile(
      leading: Container(
        padding: const EdgeInsets.all(8),
        decoration: BoxDecoration(
          color: const Color(0xFF1B3A5C).withOpacity(0.08),
          shape: BoxShape.circle,
        ),
        child: Icon(icon, color: const Color(0xFF1B3A5C), size: 20),
      ),
      title: Text(title, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w500)),
      trailing: Switch(
        value: value,
        activeColor: const Color(0xFF1B3A5C),
        onChanged: onChanged,
      ),
    );
  }
}
