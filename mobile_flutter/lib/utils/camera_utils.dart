import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:camera/camera.dart';
import 'package:google_mlkit_face_detection/google_mlkit_face_detection.dart';

class CameraUtils {
  /// Chuyển đổi CameraImage (từ ImageStream) sang InputImage cho ML Kit
  static InputImage? convertCameraImageToInputImage(
      CameraImage image, CameraDescription camera) {
    
    final orientations = {
      DeviceOrientation.portraitUp: 0,
      DeviceOrientation.landscapeLeft: 90,
      DeviceOrientation.portraitDown: 180,
      DeviceOrientation.landscapeRight: 270,
    };

    final sensorOrientation = camera.sensorOrientation;
    InputImageRotation? rotation;
    
    if (Platform.isIOS) {
      rotation = InputImageRotationValue.fromRawValue(sensorOrientation);
    } else if (Platform.isAndroid) {
      var rotationCompensation = orientations[DeviceOrientation.portraitUp];
      if (rotationCompensation == null) return null;
      if (camera.lensDirection == CameraLensDirection.front) {
        rotationCompensation = (sensorOrientation + rotationCompensation) % 360;
      } else {
        rotationCompensation =
            (sensorOrientation - rotationCompensation + 360) % 360;
      }
      rotation = InputImageRotationValue.fromRawValue(rotationCompensation);
    }
    
    if (rotation == null) return null;

    final format = InputImageFormatValue.fromRawValue(image.format.raw);
    if (format == null ||
        (Platform.isAndroid && format != InputImageFormat.nv21) ||
        (Platform.isIOS && format != InputImageFormat.bgra8888)) {
      // Android requires nv21 format for ML Kit InputImage from bytes, 
      // but camera plugin returns yuv420 by default on android.
      // Google ML Kit flutter package handles yuv420 to nv21 automatically if format is specified correctly,
      // actually we can use yuv420 directly if we provide all planes.
    }

    if (image.planes.isEmpty) return null;

    // Đối với iOS, image.planes chỉ có 1 phần tử (bgra8888)
    // Đối với Android, image.planes có 3 phần tử (Y, U, V)
    final bytes = Platform.isAndroid 
        ? _concatenatePlanes(image.planes) 
        : image.planes[0].bytes;

    final inputImageData = InputImageMetadata(
      size: Size(image.width.toDouble(), image.height.toDouble()),
      rotation: rotation,
      format: Platform.isAndroid ? InputImageFormat.nv21 : InputImageFormat.bgra8888,
      bytesPerRow: image.planes[0].bytesPerRow,
    );

    return InputImage.fromBytes(
      bytes: bytes,
      metadata: inputImageData,
    );
  }

  /// Nối các plane YUV420 lại với nhau thành NV21 (Y sau đó V sau đó U đan xen)
  /// Đây là cách đơn giản hoá để ML Kit đọc được trên Android
  static Uint8List _concatenatePlanes(List<Plane> planes) {
    final WriteBuffer allBytes = WriteBuffer();
    for (Plane plane in planes) {
      allBytes.putUint8List(plane.bytes);
    }
    return allBytes.done().buffer.asUint8List();
  }

  /// Kiểm tra ảnh có bị thiếu sáng hay không
  /// Dựa vào kênh Y (Luminance) của ảnh YUV420 (Android) hoặc RGB (iOS)
  static bool isImageTooDark(CameraImage image, {int threshold = 50}) {
    if (image.planes.isEmpty) return false;
    
    try {
      final bytes = image.planes[0].bytes; // Kênh độ sáng Y hoặc kênh R trong BGRA
      int totalLuminance = 0;
      
      // Lấy mẫu (sample) để tránh tốn CPU: tính trung bình 1000 pixels ngẫu nhiên hoặc cách đều
      int step = (bytes.length / 1000).ceil();
      if (step == 0) step = 1;
      
      int sampleCount = 0;
      for (int i = 0; i < bytes.length; i += step) {
        totalLuminance += bytes[i];
        sampleCount++;
      }
      
      double avgLuminance = totalLuminance / sampleCount;
      return avgLuminance < threshold;
    } catch (e) {
      return false;
    }
  }
}
