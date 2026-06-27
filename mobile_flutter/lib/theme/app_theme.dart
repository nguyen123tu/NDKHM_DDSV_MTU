import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class AppTheme {
  // --- Neumorphism Light Colors ---
  static const Color neuBackground = Color(0xFFE0E5EC);
  static const Color neuShadowLight = Color(0xFFFFFFFF);
  static const Color neuShadowDark = Color(0xFFA3B1C6);
  
  static const Color textDarkPrimary = Color(0xFF2D3748);
  static const Color textDarkSecondary = Color(0xFF718096);
  
  // --- Brand Colors (Dark Mode Legacy) ---
  static const Color primary = Color(0xFF64FFDA); // Xanh Ngọc (Teal)
  static const Color secondary = Color(0xFF4A90E2); // Xanh Dương (Blue)
  static const Color surfaceLight = Color(0xFF334155);
  
  static const Color success = Color(0xFF10B981);
  static const Color warning = Color(0xFFF59E0B);
  static const Color error = Color(0xFFEF4444);

  static const Color textPrimary = Color(0xFFF8FAFC);
  static const Color textSecondary = Color(0xFF94A3B8);
  static const Color accent = Color(0xFFF43F5E); 
  
  // Nền Xanh Navy Đậm
  static const Color background = Color(0xFF0A192F);
  // Nền thẻ (surface) Navy nhạt
  static const Color surface = Color(0xFF112240);
  static const Color textMuted = Color(0xFF64748B);

  // --- Glassmorphism Utilities (Legacy) ---
  static BoxDecoration glassDecoration({
    double borderRadius = 24,
    Color? color,
    double opacity = 0.1,
    bool border = true,
    BoxShape shape = BoxShape.rectangle,
  }) {
    return BoxDecoration(
      color: (color ?? Colors.white).withValues(alpha: opacity),
      borderRadius: shape == BoxShape.circle ? null : BorderRadius.circular(borderRadius),
      shape: shape,
      border: border
          ? Border.all(
              color: Colors.white.withValues(alpha: 0.1),
              width: 1,
            )
          : null,
      boxShadow: [
        BoxShadow(
          color: Colors.black.withValues(alpha: 0.2),
          blurRadius: 20,
          spreadRadius: -5,
        ),
      ],
    );
  }

  // --- Light Theme (Neumorphism Default) ---
  static ThemeData get lightTheme {
    return ThemeData(
      brightness: Brightness.light,
      scaffoldBackgroundColor: neuBackground,
      primaryColor: primary,
      colorScheme: const ColorScheme.light(
        primary: primary,
        secondary: secondary,
        surface: neuBackground,
        error: error,
      ),
      textTheme: GoogleFonts.outfitTextTheme().copyWith(
        displayLarge: GoogleFonts.outfit(color: textDarkPrimary, fontWeight: FontWeight.bold),
        displayMedium: GoogleFonts.outfit(color: textDarkPrimary, fontWeight: FontWeight.bold),
        titleLarge: GoogleFonts.outfit(color: textDarkPrimary, fontWeight: FontWeight.w600),
        titleMedium: GoogleFonts.outfit(color: textDarkPrimary, fontWeight: FontWeight.w500),
        bodyLarge: GoogleFonts.inter(color: textDarkPrimary),
        bodyMedium: GoogleFonts.inter(color: textDarkSecondary),
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: Colors.transparent,
        elevation: 0,
        centerTitle: true,
        iconTheme: IconThemeData(color: textDarkPrimary),
        titleTextStyle: TextStyle(
          color: textDarkPrimary,
          fontSize: 20,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }

  // --- Dark Theme (Legacy/Glassmorphism) ---
  static ThemeData get darkTheme {
    return ThemeData(
      brightness: Brightness.dark,
      scaffoldBackgroundColor: surface,
      primaryColor: primary,
      colorScheme: const ColorScheme.dark(
        primary: primary,
        secondary: secondary,
        surface: surface,
        error: error,
      ),
      textTheme: GoogleFonts.outfitTextTheme(ThemeData.dark().textTheme).copyWith(
        displayLarge: GoogleFonts.outfit(color: textPrimary, fontWeight: FontWeight.bold),
        displayMedium: GoogleFonts.outfit(color: textPrimary, fontWeight: FontWeight.bold),
        titleLarge: GoogleFonts.outfit(color: textPrimary, fontWeight: FontWeight.w600),
        titleMedium: GoogleFonts.outfit(color: textPrimary, fontWeight: FontWeight.w500),
        bodyLarge: GoogleFonts.inter(color: textPrimary),
        bodyMedium: GoogleFonts.inter(color: textSecondary),
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: Colors.transparent,
        elevation: 0,
        centerTitle: true,
        iconTheme: IconThemeData(color: textPrimary),
        titleTextStyle: TextStyle(
          color: textPrimary,
          fontSize: 20,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }
}
