import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../services/api_service.dart';
import 'package:http/http.dart' as http;
import 'dart:typed_data';

/// Widget chuyên dụng để hiển thị ảnh từ API có kèm Bearer token
class ApiImage extends StatefulWidget {
  final String path;
  final BoxFit fit;
  final double? width;
  final double? height;
  final Widget? placeholder;
  final Widget? errorWidget;

  const ApiImage({
    super.key,
    required this.path,
    this.fit = BoxFit.cover,
    this.width,
    this.height,
    this.placeholder,
    this.errorWidget,
  });

  @override
  State<ApiImage> createState() => _ApiImageState();
}

class _ApiImageState extends State<ApiImage> {
  Uint8List? _imageBytes;
  bool _hasError = false;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadImage();
  }
  
  @override
  void didUpdateWidget(ApiImage oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.path != widget.path) {
      _loadImage();
    }
  }

  Future<void> _loadImage() async {
    if (widget.path.isEmpty) {
      if (mounted) {
        setState(() {
          _hasError = true;
          _isLoading = false;
        });
      }
      return;
    }
    
    try {
      if (mounted) setState(() { _isLoading = true; _hasError = false; });
      
      final prefs = await SharedPreferences.getInstance();
      final token = prefs.getString('auth_token');
      
      String cleanPath = widget.path;
      if (cleanPath.startsWith('/')) cleanPath = cleanPath.substring(1);
      
      final url = cleanPath.startsWith('http') 
          ? cleanPath 
          : '${ApiService.baseUrl}/$cleanPath';
      
      final response = await http.get(
        Uri.parse(url),
        headers: {
          if (token != null) 'Authorization': 'Bearer $token',
          'ngrok-skip-browser-warning': '69420',
        },
      ).timeout(const Duration(seconds: 15));
      
      if (response.statusCode == 200 && mounted) {
        setState(() {
          _imageBytes = response.bodyBytes;
          _isLoading = false;
        });
      } else {
        if (mounted) setState(() { _hasError = true; _isLoading = false; });
      }
    } catch (e) {
      if (mounted) setState(() { _hasError = true; _isLoading = false; });
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return widget.placeholder ?? SizedBox(
        width: widget.width,
        height: widget.height,
        child: const Center(child: CircularProgressIndicator(strokeWidth: 2)),
      );
    }
    
    if (_hasError || _imageBytes == null) {
      return widget.errorWidget ?? SizedBox(
        width: widget.width,
        height: widget.height,
        child: const Center(child: Icon(Icons.broken_image, color: Colors.grey)),
      );
    }
    
    return Image.memory(
      _imageBytes!,
      fit: widget.fit,
      width: widget.width,
      height: widget.height,
    );
  }
}
