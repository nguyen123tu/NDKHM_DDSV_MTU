import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'providers/auth_provider.dart';
import 'providers/attendance_provider.dart';
import 'providers/connectivity_provider.dart';
import 'screens/login_screen.dart';
import 'screens/home_screen.dart';

import 'services/sync_manager.dart';
import 'services/firebase_messaging_service.dart'; // Thêm import FCM
import 'theme/app_theme.dart'; // Thêm import theme
import 'package:firebase_core/firebase_core.dart'; // Thêm import Firebase Core

/// Firebase init chạy ngầm, không block UI
Future<void> _initFirebase() async {
  try {
    await Firebase.initializeApp().timeout(const Duration(seconds: 5));
    await FirebaseMessagingService().init().timeout(const Duration(seconds: 5));
    debugPrint("Firebase initialized successfully");
  } catch (e) {
    debugPrint("Firebase init failed (non-blocking): $e");
  }
}

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Kích hoạt đồng bộ ngầm khi mở app (non-blocking, fire-and-forget)
  SyncManager.instance.syncAll().catchError((e) {
    debugPrint("SyncAll background error: $e");
  });
  
  // Khởi tạo Firebase Cloud Messaging (FCM) - non-blocking với timeout
  _initFirebase(); // fire-and-forget, không await

  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AuthProvider()..checkAuthStatus()),
        ChangeNotifierProvider(create: (_) => AttendanceProvider()),
        ChangeNotifierProvider(create: (_) => ConnectivityProvider()),
      ],
      child: const FaceAttendanceApp(),
    ),
  );
}

class FaceAttendanceApp extends StatelessWidget {
  const FaceAttendanceApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'MTU Kiosk Face Attendance',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.darkTheme, // Áp dụng Dark Theme
      home: Consumer<AuthProvider>(
        builder: (context, auth, _) {
          return auth.isAuthenticated ? const HomeScreen() : const LoginScreen();
        },
      ),
    );
  }
}
