import 'package:flutter/material.dart';
import 'neu_container.dart';
import '../theme/app_theme.dart';

class NeuButton extends StatefulWidget {
  final Widget child;
  final VoidCallback? onPressed;
  final double borderRadius;
  final EdgeInsetsGeometry padding;
  final BoxShape shape;
  final bool isPrimary; // Nếu là primary button, thay vì nền thường sẽ có nền màu gradient hoặc icon màu nổi

  const NeuButton({
    super.key,
    required this.child,
    this.onPressed,
    this.borderRadius = 16,
    this.padding = const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
    this.shape = BoxShape.rectangle,
    this.isPrimary = false,
  });

  @override
  State<NeuButton> createState() => _NeuButtonState();
}

class _NeuButtonState extends State<NeuButton> {
  bool _isPressed = false;

  void _handleTapDown(TapDownDetails details) {
    if (widget.onPressed != null) {
      setState(() => _isPressed = true);
    }
  }

  void _handleTapUp(TapUpDetails details) {
    if (widget.onPressed != null) {
      setState(() => _isPressed = false);
      widget.onPressed!();
    }
  }

  void _handleTapCancel() {
    if (widget.onPressed != null) {
      setState(() => _isPressed = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    
    Widget content = widget.child;

    return GestureDetector(
      onTapDown: _handleTapDown,
      onTapUp: _handleTapUp,
      onTapCancel: _handleTapCancel,
      child: AnimatedScale(
        scale: _isPressed ? 0.95 : 1.0,
        duration: const Duration(milliseconds: 100),
        child: NeuContainer(
          borderRadius: widget.borderRadius,
          shape: widget.shape,
          padding: widget.padding,
          isPressed: _isPressed,
          child: DefaultTextStyle(
            style: Theme.of(context).textTheme.titleMedium!.copyWith(
              color: widget.isPrimary ? (isDark ? AppTheme.secondary : AppTheme.primary) : (isDark ? Colors.white : AppTheme.textDarkPrimary),
            ),
            child: IconTheme(
              data: IconThemeData(
                color: widget.isPrimary ? (isDark ? AppTheme.secondary : AppTheme.primary) : (isDark ? Colors.white : AppTheme.textDarkPrimary),
              ),
              child: content,
            ),
          ),
        ),
      ),
    );
  }
}
