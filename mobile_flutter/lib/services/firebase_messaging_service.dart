import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'api_service.dart'; // import api_service để gọi update fcm_token

// Hàm xử lý thông báo khi app ở dưới nền (Background/Terminated)
@pragma('vm:entry-point')
Future<void> _firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  await Firebase.initializeApp();
  debugPrint("Handling a background message: ${message.messageId}");
}

class FirebaseMessagingService {
  static final FirebaseMessagingService _instance =
      FirebaseMessagingService._internal();
  factory FirebaseMessagingService() => _instance;
  FirebaseMessagingService._internal();

  final FirebaseMessaging _fcm = FirebaseMessaging.instance;

  Future<void> init() async {
    // Xin quyền người dùng (chủ yếu cho iOS, Android 13+)
    NotificationSettings settings = await _fcm.requestPermission(
      alert: true,
      announcement: false,
      badge: true,
      carPlay: false,
      criticalAlert: false,
      provisional: false,
      sound: true,
    );

    debugPrint('User granted permission: ${settings.authorizationStatus}');

    // Đăng ký Background handler
    FirebaseMessaging.onBackgroundMessage(_firebaseMessagingBackgroundHandler);

    // Lắng nghe khi app đang mở (Foreground)
    FirebaseMessaging.onMessage.listen((RemoteMessage message) {
      debugPrint('Got a message whilst in the foreground!');
      debugPrint('Message data: ${message.data}');

      if (message.notification != null) {
        debugPrint(
            'Message also contained a notification: ${message.notification}');
        // Hiện tại chỉ in ra, có thể dùng flutter_local_notifications để hiện popup nếu cần
      }
    });

    // Lấy Token của thiết bị
    await updateDeviceToken();
  }

  Future<void> updateDeviceToken() async {
    try {
      String? token = await _fcm.getToken();
      debugPrint("FCM Token: $token");
      if (token != null) {
        // Lưu lại token vào server
        final prefs = await SharedPreferences.getInstance();
        final jwt = prefs.getString('auth_token');
        if (jwt != null && jwt.isNotEmpty) {
          await ApiService().updateFcmToken(token);
        }
      }
    } catch (e) {
      debugPrint("Lỗi khi lấy FCM Token: $e");
    }
  }
}
