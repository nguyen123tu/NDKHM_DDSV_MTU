import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

class NeuButton extends StatefulWidget {
  final Widget child;
  final VoidCallback? onPressed;
  final double borderRadius;
  final EdgeInsetsGeometry padding;
  final BoxShape shape;
  final bool isPrimary; // Primary = Gradient Background

  const NeuButton({
    super.key,
    required this.child,
    this.onPressed,
    this.borderRadius = 30, // Pill shape default
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
    Widget content = widget.child;

    return GestureDetector(
      onTapDown: _handleTapDown,
      onTapUp: _handleTapUp,
      onTapCancel: _handleTapCancel,
      child: AnimatedScale(
        scale: _isPressed ? 0.92 : 1.0,
        duration: const Duration(milliseconds: 100),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 150),
          padding: widget.padding,
          decoration: BoxDecoration(
            shape: widget.shape,
            borderRadius: widget.shape == BoxShape.circle ? null : BorderRadius.circular(widget.borderRadius),
            gradient: widget.isPrimary ? AppTheme.primaryGradient : null,
            color: widget.isPrimary ? null : AppTheme.surfaceLight,
            boxShadow: widget.isPrimary && !_isPressed ? [
              BoxShadow(
                color: AppTheme.primary.withOpacity(0.4),
                blurRadius: 20,
                offset: const Offset(0, 8),
              )
            ] : null,
          ),
          child: DefaultTextStyle(
            style: Theme.of(context).textTheme.titleMedium!.copyWith(
              color: Colors.white,
              fontWeight: FontWeight.bold,
            ),
            child: IconTheme(
              data: const IconThemeData(color: Colors.white),
              child: content,
            ),
          ),
        ),
      ),
    );
  }
}
