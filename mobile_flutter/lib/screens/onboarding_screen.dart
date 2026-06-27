import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import '../theme/app_theme.dart';
import '../widgets/neu_container.dart';
import '../widgets/neu_button.dart';
class OnboardingScreen extends StatefulWidget {
  const OnboardingScreen({super.key});

  @override
  _OnboardingScreenState createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends State<OnboardingScreen> {
  final PageController _pageController = PageController();
  int _currentPage = 0;

  final List<Map<String, dynamic>> _pages = [
    {
      "title": "NHẬN DIỆN KHUÔN MẶT\nTỰ ĐỘNG",
      "subtitle": "Nhận diện khuôn mặt tự động, thông báo kết quả kèm hình ảnh tức thì qua ứng dụng của phụ huynh",
      "icon": Icons.face_retouching_natural,
      "color": AppTheme.primary,
    },
    {
      "title": "XÁC THỰC\nKHUÔN MẶT",
      "subtitle": "Giảm thiểu tối đa sai sót với độ chính xác lên tới 99,99% cùng với tính năng Liveness Face",
      "icon": Icons.security,
      "color": AppTheme.secondary,
    },
    {
      "title": "THÔNG BÁO ĐIỂM DANH\nTHÀNH CÔNG",
      "subtitle": "Ứng dụng gửi thông báo kết quả ngay khi điểm danh thành công",
      "icon": Icons.mark_email_read,
      "color": AppTheme.success,
    },
  ];

  void _completeOnboarding() {
    // Dùng AuthProvider để cập nhật trạng thái,
    // Consumer ở main.dart sẽ tự động chuyển sang LoginScreen
    Provider.of<AuthProvider>(context, listen: false).setOnboardingSeen();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        color: Theme.of(context).scaffoldBackgroundColor,
        child: SafeArea(
          child: Column(
            children: [
              // Nút Bỏ qua
              Align(
                alignment: Alignment.topRight,
                child: TextButton(
                  onPressed: _completeOnboarding,
                  child: const Text("Bỏ qua", style: TextStyle(color: AppTheme.textSecondary)),
                ),
              ),

              // Nội dung trượt
              Expanded(
                child: PageView.builder(
                  controller: _pageController,
                  onPageChanged: (int page) {
                    setState(() {
                      _currentPage = page;
                    });
                  },
                  itemCount: _pages.length,
                  itemBuilder: (context, index) {
                    return Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 40.0),
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          // Ảnh/Icon minh họa
                          NeuContainer(
                            padding: const EdgeInsets.all(50),
                            shape: BoxShape.circle,
                            child: Icon(
                              _pages[index]["icon"],
                              size: 120,
                              color: _pages[index]["color"],
                            ),
                          ),
                          const SizedBox(height: 50),
                          
                          // Tiêu đề
                          Text(
                            _pages[index]["title"],
                            textAlign: TextAlign.center,
                            style: const TextStyle(
                              fontSize: 24,
                              fontWeight: FontWeight.bold,
                              color: AppTheme.textPrimary,
                              height: 1.3,
                            ),
                          ),
                          const SizedBox(height: 20),
                          
                          // Phụ đề
                          Text(
                            _pages[index]["subtitle"],
                            textAlign: TextAlign.center,
                            style: const TextStyle(
                              fontSize: 15,
                              color: AppTheme.textSecondary,
                              height: 1.5,
                            ),
                          ),
                        ],
                      ),
                    );
                  },
                ),
              ),

              // Chấm trang (Dots)
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: List.generate(
                  _pages.length,
                  (index) => buildDot(index, context),
                ),
              ),
              
              const SizedBox(height: 30),

              // Nút Tiếp Tục / Bắt Đầu
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 40.0, vertical: 20),
                child: SizedBox(
                  width: double.infinity,
                  child: NeuButton(
                    isPrimary: true,
                    onPressed: () {
                      if (_currentPage == _pages.length - 1) {
                        _completeOnboarding();
                      } else {
                        _pageController.nextPage(
                          duration: const Duration(milliseconds: 300),
                          curve: Curves.easeIn,
                        );
                      }
                    },
                    child: Center(
                      child: Text(
                        _currentPage == _pages.length - 1 ? "Bắt Đầu Ngay" : "Tiếp tục",
                        style: const TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                          color: Colors.white,
                        ),
                      ),
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 20),
            ],
          ),
        ),
      ),
    );
  }

  Widget buildDot(int index, BuildContext context) {
    return Container(
      height: 10,
      width: _currentPage == index ? 25 : 10,
      margin: const EdgeInsets.only(right: 5),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(20),
        color: _currentPage == index ? AppTheme.primary : AppTheme.textMuted.withValues(alpha: 0.3),
      ),
    );
  }
}
