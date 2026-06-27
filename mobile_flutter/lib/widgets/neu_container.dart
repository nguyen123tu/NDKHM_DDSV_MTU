import 'dart:ui';
import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

class NeuContainer extends StatelessWidget {
  final Widget child;
  final double borderRadius;
  final EdgeInsetsGeometry? padding;
  final EdgeInsetsGeometry? margin;
  final double? width;
  final double? height;
  final bool isPressed;
  final BoxShape shape;

  const NeuContainer({
    super.key,
    required this.child,
    this.borderRadius = 20,
    this.padding,
    this.margin,
    this.width,
    this.height,
    this.isPressed = false,
    this.shape = BoxShape.rectangle,
  });

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    
    // Glassmorphism cho nền tối
    final Color bgColor = isDark
        ? (isPressed ? Colors.black.withValues(alpha: 0.2) : Colors.white.withValues(alpha: 0.05))
        : (isPressed ? const Color(0xFFE2E8F0) : AppTheme.neuBackground);
        
    final Color borderColor = isDark
        ? (isPressed ? Colors.black.withValues(alpha: 0.3) : Colors.white.withValues(alpha: 0.1))
        : (isPressed ? Colors.grey.withValues(alpha: 0.3) : Colors.transparent);

    final List<BoxShadow> lightModeShadows = isPressed
        ? []
        : [
            BoxShadow(
              color: AppTheme.neuShadowDark,
              offset: const Offset(4, 4),
              blurRadius: 10,
              spreadRadius: 1,
            ),
            BoxShadow(
              color: AppTheme.neuShadowLight,
              offset: const Offset(-4, -4),
              blurRadius: 10,
              spreadRadius: 1,
            ),
          ];

    Widget container = AnimatedContainer(
      duration: const Duration(milliseconds: 150),
      curve: Curves.easeOut,
      width: width,
      height: height,
      margin: margin,
      padding: padding,
      decoration: BoxDecoration(
        color: bgColor,
        shape: shape,
        borderRadius: shape == BoxShape.circle ? null : BorderRadius.circular(borderRadius),
        border: Border.all(color: borderColor, width: 1.5),
        boxShadow: isDark ? [] : lightModeShadows,
      ),
      child: child,
    );

    if (isDark) {
      return ClipRRect(
        borderRadius: shape == BoxShape.circle ? BorderRadius.circular(1000) : BorderRadius.circular(borderRadius),
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
          child: container,
        ),
      );
    }
    return container;
  }
}
