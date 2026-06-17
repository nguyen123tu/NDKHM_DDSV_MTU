import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../theme/app_theme.dart';
import '../services/api_service.dart';

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

  final _serverUrlCtrl = TextEditingController();
  bool _testingConnection = false;

  @override
  void initState() {
    super.initState();
    _loadSettings();
  }

  @override
  void dispose() {
    _serverUrlCtrl.dispose();
    super.dispose();
  }

  Future<void> _loadSettings() async {
    final prefs = await SharedPreferences.getInstance();
    final currentUrl = await ApiService.getServerUrl();
    setState(() {
      _threshold = prefs.getDouble('ai_threshold') ?? 0.45;
      _allowMask = prefs.getBool('allow_mask') ?? true;
      _antiFake = prefs.getBool('anti_fake') ?? false;
      _canAdjust = prefs.getBool('can_adjust_threshold') ?? true;
      _serverUrlCtrl.text = currentUrl;
    });
  }

  Future<void> _saveSettings() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setDouble('ai_threshold', _threshold);
    await prefs.setBool('allow_mask', _allowMask);
    await prefs.setBool('anti_fake', _antiFake);
    await prefs.setBool('can_adjust_threshold', _canAdjust);

    // Lưu Server URL
    await ApiService.setServerUrl(_serverUrlCtrl.text);

    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text("Đã lưu cấu hình ✓"),
          backgroundColor: AppTheme.success,
        ),
      );
    }
  }

  Future<void> _testConnection() async {
    setState(() => _testingConnection = true);
    try {
      final url = _serverUrlCtrl.text.trim();
      final uri = Uri.parse('$url/api/mobile/classes');
      final response = await ApiService().getClasses();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text("✓ Kết nối thành công! (${response.length} lớp)"),
            backgroundColor: AppTheme.success,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text("✗ ${ApiService.friendlyError(e)}"),
            backgroundColor: AppTheme.error,
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _testingConnection = false);
    }
  }

  Future<void> _resetServerUrl() async {
    await ApiService.resetServerUrl();
    final newUrl = await ApiService.getServerUrl();
    setState(() => _serverUrlCtrl.text = newUrl);
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
            content: Text("Đã đặt lại URL mặc định"),
            backgroundColor: AppTheme.secondary),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: AppBar(
        title: const Text("Cấu hình hệ thống",
            style: TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: Colors.transparent,
        foregroundColor: AppTheme.textPrimary,
        elevation: 0,
      ),
      body: Stack(
        children: [
          // Ambient glow
          Positioned(
            top: -100,
            right: -100,
            child: ImageFiltered(
              imageFilter: ImageFilter.blur(sigmaX: 80, sigmaY: 80),
              child: Container(
                width: 300,
                height: 300,
                decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: AppTheme.primary.withOpacity(0.15)),
              ),
            ),
          ),

          SingleChildScrollView(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // ====== SERVER URL CONFIG ======
                const Text(
                  "CẤU HÌNH SERVER",
                  style: TextStyle(
                      color: AppTheme.textSecondary,
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                      letterSpacing: 1),
                ),
                const SizedBox(height: 12),
                Container(
                  padding: const EdgeInsets.all(20),
                  decoration:
                      AppTheme.glassDecoration(borderRadius: 20, opacity: 0.05),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      TextField(
                        controller: _serverUrlCtrl,
                        style: const TextStyle(
                            color: AppTheme.textPrimary,
                            fontSize: 14,
                            fontFamily: 'monospace'),
                        decoration: InputDecoration(
                          labelText: "URL Server",
                          labelStyle: const TextStyle(
                              color: AppTheme.textSecondary, fontSize: 14),
                          hintText: "https://example.ngrok-free.dev",
                          hintStyle: TextStyle(
                              color: AppTheme.textMuted.withOpacity(0.5)),
                          prefixIcon: const Icon(Icons.link,
                              color: AppTheme.secondary, size: 20),
                          filled: true,
                          fillColor: Colors.white.withOpacity(0.05),
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
                      ),
                      const SizedBox(height: 12),
                      Row(
                        children: [
                          Expanded(
                            child: OutlinedButton.icon(
                              onPressed:
                                  _testingConnection ? null : _testConnection,
                              icon: _testingConnection
                                  ? const SizedBox(
                                      width: 16,
                                      height: 16,
                                      child: CircularProgressIndicator(
                                          color: AppTheme.secondary,
                                          strokeWidth: 2))
                                  : const Icon(Icons.wifi_find, size: 18),
                              label: Text(_testingConnection
                                  ? "Đang kiểm tra..."
                                  : "Test kết nối"),
                              style: OutlinedButton.styleFrom(
                                foregroundColor: AppTheme.secondary,
                                side:
                                    const BorderSide(color: AppTheme.secondary),
                                shape: RoundedRectangleBorder(
                                    borderRadius: BorderRadius.circular(12)),
                                padding:
                                    const EdgeInsets.symmetric(vertical: 12),
                              ),
                            ),
                          ),
                          const SizedBox(width: 12),
                          OutlinedButton.icon(
                            onPressed: _resetServerUrl,
                            icon: const Icon(Icons.restore, size: 18),
                            label: const Text("Mặc định"),
                            style: OutlinedButton.styleFrom(
                              foregroundColor: AppTheme.textMuted,
                              side: BorderSide(
                                  color: AppTheme.textMuted.withOpacity(0.5)),
                              shape: RoundedRectangleBorder(
                                  borderRadius: BorderRadius.circular(12)),
                              padding: const EdgeInsets.symmetric(vertical: 12),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ).animate().fadeIn(duration: 400.ms).slideY(begin: 0.1, end: 0),

                const SizedBox(height: 28),

                // ====== AI THRESHOLD ======
                const Text(
                  "CẤU HÌNH AI",
                  style: TextStyle(
                      color: AppTheme.textSecondary,
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                      letterSpacing: 1),
                ),
                const SizedBox(height: 12),
                Container(
                  padding:
                      const EdgeInsets.symmetric(vertical: 24, horizontal: 20),
                  decoration:
                      AppTheme.glassDecoration(borderRadius: 20, opacity: 0.05),
                  child: Column(
                    children: [
                      // Gauge
                      Center(
                        child: SizedBox(
                          width: 160,
                          height: 160,
                          child: Stack(
                            alignment: Alignment.center,
                            children: [
                              SizedBox(
                                width: 140,
                                height: 140,
                                child: CircularProgressIndicator(
                                  value: _threshold,
                                  strokeWidth: 10,
                                  backgroundColor:
                                      Colors.white.withOpacity(0.08),
                                  color: _threshold > 0.6
                                      ? AppTheme.success
                                      : _threshold > 0.3
                                          ? AppTheme.secondary
                                          : AppTheme.error,
                                ),
                              ),
                              Column(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  Text(
                                    "${(_threshold * 100).toInt()}%",
                                    style: const TextStyle(
                                        fontSize: 32,
                                        fontWeight: FontWeight.bold,
                                        color: AppTheme.textPrimary),
                                  ),
                                  const Text("Ngưỡng AI",
                                      style: TextStyle(
                                          color: AppTheme.textSecondary,
                                          fontSize: 12)),
                                ],
                              ),
                            ],
                          ),
                        ),
                      ),
                      const SizedBox(height: 16),
                      Slider(
                        value: _threshold,
                        min: 0.1,
                        max: 0.9,
                        divisions: 80,
                        activeColor: AppTheme.secondary,
                        inactiveColor: Colors.white.withOpacity(0.1),
                        onChanged: _canAdjust
                            ? (val) => setState(() => _threshold = val)
                            : null,
                      ),
                      TextButton(
                        onPressed: () => setState(() => _threshold = 0.45),
                        child: const Text("Đặt lại mặc định (45%)",
                            style: TextStyle(
                                color: AppTheme.textMuted, fontSize: 13)),
                      ),
                    ],
                  ),
                ).animate().fadeIn(delay: 200.ms).slideY(begin: 0.1, end: 0),

                const SizedBox(height: 20),

                // ====== TOGGLE SETTINGS ======
                Container(
                  decoration:
                      AppTheme.glassDecoration(borderRadius: 20, opacity: 0.05),
                  child: Column(
                    children: [
                      _buildToggleTile(
                        icon: Icons.edit_attributes,
                        title: "Cho phép điều chỉnh ngưỡng",
                        subtitle: "Bật/tắt slider ngưỡng AI",
                        value: _canAdjust,
                        onChanged: (v) => setState(() => _canAdjust = v),
                      ),
                      Divider(
                          height: 1,
                          color: Colors.white.withOpacity(0.06),
                          indent: 60),
                      _buildToggleTile(
                        icon: Icons.face_retouching_natural,
                        title: "Cho phép mặt bị che",
                        subtitle: "Nhận diện khi đeo khẩu trang",
                        value: _allowMask,
                        onChanged: (v) => setState(() => _allowMask = v),
                      ),
                      Divider(
                          height: 1,
                          color: Colors.white.withOpacity(0.06),
                          indent: 60),
                      _buildToggleTile(
                        icon: Icons.security,
                        title: "Chống Fake (Liveness)",
                        subtitle: "Anti-Spoofing MiniFASNet",
                        value: _antiFake,
                        onChanged: (v) => setState(() => _antiFake = v),
                      ),
                    ],
                  ),
                ).animate().fadeIn(delay: 400.ms).slideY(begin: 0.1, end: 0),

                const SizedBox(height: 32),

                // ====== SAVE BUTTON ======
                SizedBox(
                  width: double.infinity,
                  height: 56,
                  child: Container(
                    decoration: BoxDecoration(
                      gradient: const LinearGradient(
                          colors: [AppTheme.primary, Color(0xFF7C3AED)]),
                      borderRadius: BorderRadius.circular(16),
                      boxShadow: [
                        BoxShadow(
                            color: AppTheme.primary.withOpacity(0.4),
                            blurRadius: 12,
                            offset: const Offset(0, 6)),
                      ],
                    ),
                    child: ElevatedButton.icon(
                      onPressed: _saveSettings,
                      icon: const Icon(Icons.save, color: Colors.white),
                      label: const Text("LƯU CẤU HÌNH",
                          style: TextStyle(
                              color: Colors.white,
                              fontWeight: FontWeight.bold,
                              fontSize: 16,
                              letterSpacing: 1)),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.transparent,
                        shadowColor: Colors.transparent,
                        shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(16)),
                      ),
                    ),
                  ),
                )
                    .animate()
                    .fadeIn(delay: 600.ms)
                    .scale(begin: const Offset(0.95, 0.95)),

                const SizedBox(height: 40),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildToggleTile({
    required IconData icon,
    required String title,
    required String subtitle,
    required bool value,
    required Function(bool) onChanged,
  }) {
    return ListTile(
      contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 4),
      leading: Container(
        padding: const EdgeInsets.all(10),
        decoration: BoxDecoration(
          color: (value ? AppTheme.secondary : AppTheme.textMuted)
              .withOpacity(0.15),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Icon(icon,
            color: value ? AppTheme.secondary : AppTheme.textMuted, size: 20),
      ),
      title: Text(title,
          style: const TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.w600,
              color: AppTheme.textPrimary)),
      subtitle: Text(subtitle,
          style: const TextStyle(fontSize: 11, color: AppTheme.textMuted)),
      trailing: Switch(
        value: value,
        activeThumbColor: AppTheme.secondary,
        inactiveTrackColor: Colors.white.withOpacity(0.1),
        onChanged: onChanged,
      ),
    );
  }
}
