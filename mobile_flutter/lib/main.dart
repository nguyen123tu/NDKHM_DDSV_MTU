import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'providers/auth_provider.dart';
import 'providers/attendance_provider.dart';
import 'providers/connectivity_provider.dart';
import 'screens/login_screen.dart';
import 'screens/home_screen.dart';
import 'screens/onboarding_screen.dart';
import 'services/sync_manager.dart';
import 'services/firebase_messaging_service.dart'; // Thêm import FCM
import 'theme/app_theme.dart'; // Thêm import theme
import 'package:firebase_core/firebase_core.dart'; // Thêm import Firebase Core

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Bật bộ lắng nghe mạng để đồng bộ Offline-First
  SyncManager.instance.initializeNetworkListener();
  // Kích hoạt đồng bộ ngay khi vừa mở app
  SyncManager.instance.syncAll();
  
  // Khởi tạo Firebase Cloud Messaging (FCM)
  try {
    await Firebase.initializeApp();
    await FirebaseMessagingService().init();
  } catch(e) {
    debugPrint("Firebase init failed: \$e");
  }

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
          if (!auth.hasSeenOnboarding) {
            return const OnboardingScreen();
          }
          return auth.isAuthenticated ? const HomeScreen() : const LoginScreen();
        },
      ),
    );
  }
}
