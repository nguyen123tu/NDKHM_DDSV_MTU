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
    this.borderRadius = 24,
    this.padding,
    this.margin,
    this.width,
    this.height,
    this.isPressed = false,
    this.shape = BoxShape.rectangle,
  });

  @override
  Widget build(BuildContext context) {
    // --- Modern Dark Card (Slate 800) ---
    // If isPressed, make it look slightly darker (inner shadow effect simulated by background color)
    final Color bgColor = isPressed ? AppTheme.background : AppTheme.surface;
    final Color borderColor = isPressed
        ? Colors.white.withOpacity(0.05)
        : Colors.white.withOpacity(0.08);

    return AnimatedContainer(
      duration: const Duration(milliseconds: 150),
      curve: Curves.easeOut,
      width: width,
      height: height,
      margin: margin,
      padding: padding,
      decoration: BoxDecoration(
        color: bgColor,
        shape: shape,
        borderRadius: shape == BoxShape.circle
            ? null
            : BorderRadius.circular(borderRadius),
        border: Border.all(color: borderColor, width: 1),
        boxShadow: isPressed
            ? []
            : [
                BoxShadow(
                  color: Colors.black.withOpacity(0.25),
                  blurRadius: 15,
                  offset: const Offset(0, 8),
                ),
              ],
      ),
      child: child,
    );
  }
}
