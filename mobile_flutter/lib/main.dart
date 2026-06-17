import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'providers/auth_provider.dart';
import 'providers/attendance_provider.dart';
import 'providers/connectivity_provider.dart';
import 'screens/login_screen.dart';
import 'screens/main_screen.dart';
import 'screens/splash_screen.dart';
import 'screens/onboarding_screen.dart';

import 'services/sync_manager.dart';
import 'services/api_service.dart';
import 'services/firebase_messaging_service.dart';
import 'theme/app_theme.dart';
import 'package:firebase_core/firebase_core.dart';

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

  // Khởi tạo baseUrl từ SharedPreferences (nếu user đã tùy chỉnh)
  await ApiService.initBaseUrl();

  // Kích hoạt đồng bộ ngầm khi mở app (non-blocking, fire-and-forget)
  SyncManager.instance.syncAll().catchError((e) {
    debugPrint("SyncAll background error: $e");
  });

  // Khởi tạo Firebase Cloud Messaging (FCM) - non-blocking với timeout
  _initFirebase(); // fire-and-forget, không await

  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(
            create: (_) => AuthProvider()..checkAuthStatus()),
        ChangeNotifierProvider(create: (_) => AttendanceProvider()),
        ChangeNotifierProvider(create: (_) => ConnectivityProvider()),
      ],
      child: const FaceAttendanceApp(),
    ),
  );
}

class FaceAttendanceApp extends StatefulWidget {
  const FaceAttendanceApp({super.key});

  @override
  State<FaceAttendanceApp> createState() => _FaceAttendanceAppState();
}

class _FaceAttendanceAppState extends State<FaceAttendanceApp> {
  bool _showSplash = true;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'MTU Face Attendance',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.darkTheme,
      home: _showSplash
          ? SplashScreen(
              onComplete: () {
                if (mounted) setState(() => _showSplash = false);
              },
            )
          : Consumer<AuthProvider>(
              builder: (context, auth, _) {
                if (auth.isAuthenticated) {
                  return const MainScreen(); // Thay vì HomeScreen
                }
                if (!auth.hasSeenOnboarding) {
                  return const OnboardingScreen();
                }
                return const LoginScreen();
              },
            ),
    );
  }
}
