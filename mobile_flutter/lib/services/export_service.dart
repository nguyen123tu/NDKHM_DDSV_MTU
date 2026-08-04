import 'dart:io';
import 'package:excel/excel.dart';
import 'package:path_provider/path_provider.dart';
import 'package:share_plus/share_plus.dart';
import 'package:flutter/foundation.dart' show kIsWeb;

/// Dịch vụ xuất báo cáo Excel cho Mobile.
/// Hỗ trợ cả Map<String, dynamic> và Model objects.
class ExportService {
  /// Helper: Lấy giá trị từ record (hỗ trợ cả Map và Model)
  static String _getField(dynamic record, String mapKey) {
    if (record is Map) {
      return (record[mapKey] ?? '').toString();
    }
    try {
      switch (mapKey) {
        case 'mssv':
          return record.mssv?.toString() ?? '';
        case 'ho_ten':
          return record.hoTen?.toString() ?? '';
        case 'ma_lop':
          return record.maLop?.toString() ?? '';
        case 'thoi_gian':
          return record.thoiGian?.toString() ?? '';
        case 'trang_thai':
          return record.trangThai?.toString() ?? '';
        default:
          return '';
      }
    } catch (_) {
      return '';
    }
  }

  static Future<void> exportAttendanceToExcel(List<dynamic> history) async {
    if (kIsWeb || history.isEmpty) return;

    var excel = Excel.createExcel();
    Sheet sheetObject = excel['Báo cáo điểm danh'];
    excel.delete('Sheet1');

    CellStyle headerStyle = CellStyle(
      backgroundColorHex: ExcelColor.fromHexString('#1B3A5C'),
      fontColorHex: ExcelColor.fromHexString('#FFFFFF'),
      bold: true,
      horizontalAlign: HorizontalAlign.Center,
    );

    List<String> headers = [
      "STT",
      "MSSV",
      "Họ và Tên",
      "Lớp",
      "Thời gian",
      "Trạng thái"
    ];
    for (var i = 0; i < headers.length; i++) {
      var cell = sheetObject
          .cell(CellIndex.indexByColumnRow(columnIndex: i, rowIndex: 0));
      cell.value = TextCellValue(headers[i]);
      cell.cellStyle = headerStyle;
    }

    for (int i = 0; i < history.length; i++) {
      final record = history[i];
      int row = i + 1;

      sheetObject
          .cell(CellIndex.indexByColumnRow(columnIndex: 0, rowIndex: row))
          .value = IntCellValue(i + 1);
      sheetObject
          .cell(CellIndex.indexByColumnRow(columnIndex: 1, rowIndex: row))
          .value = TextCellValue(_getField(record, 'mssv'));
      sheetObject
          .cell(CellIndex.indexByColumnRow(columnIndex: 2, rowIndex: row))
          .value = TextCellValue(_getField(record, 'ho_ten'));
      sheetObject
          .cell(CellIndex.indexByColumnRow(columnIndex: 3, rowIndex: row))
          .value = TextCellValue(_getField(record, 'ma_lop'));
      sheetObject
          .cell(CellIndex.indexByColumnRow(columnIndex: 4, rowIndex: row))
          .value = TextCellValue(_getField(record, 'thoi_gian'));
      sheetObject
          .cell(CellIndex.indexByColumnRow(columnIndex: 5, rowIndex: row))
          .value = TextCellValue(_getField(record, 'trang_thai'));
    }

    var fileBytes = excel.save();
    if (fileBytes == null) return;

    final String fileName =
        'Bao_cao_diem_danh_${DateTime.now().millisecondsSinceEpoch}.xlsx';
    final directory = await getApplicationDocumentsDirectory();
    final String filePath = '${directory.path}/$fileName';

    final file = File(filePath);
    await file.create(recursive: true);
    await file.writeAsBytes(fileBytes);

    await Share.shareXFiles([XFile(filePath)],
        text: 'Báo cáo điểm danh MTUFace');
  }

  static Future<void> exportSessionToExcel(
      List<dynamic> students, String tenLop) async {
    if (kIsWeb || students.isEmpty) return;

    var excel = Excel.createExcel();
    Sheet sheetObject = excel['Báo cáo điểm danh'];
    excel.delete('Sheet1');

    CellStyle headerStyle = CellStyle(
      backgroundColorHex: ExcelColor.fromHexString('#1B3A5C'),
      fontColorHex: ExcelColor.fromHexString('#FFFFFF'),
      bold: true,
      horizontalAlign: HorizontalAlign.Center,
    );

    List<String> headers = [
      "STT",
      "MSSV",
      "Họ và Tên",
      "Trạng thái",
      "Thời gian"
    ];
    for (var i = 0; i < headers.length; i++) {
      var cell = sheetObject
          .cell(CellIndex.indexByColumnRow(columnIndex: i, rowIndex: 0));
      cell.value = TextCellValue(headers[i]);
      cell.cellStyle = headerStyle;
    }

    for (int i = 0; i < students.length; i++) {
      final student = students[i];
      int row = i + 1;

      sheetObject
          .cell(CellIndex.indexByColumnRow(columnIndex: 0, rowIndex: row))
          .value = IntCellValue(i + 1);
      sheetObject
          .cell(CellIndex.indexByColumnRow(columnIndex: 1, rowIndex: row))
          .value = TextCellValue(student['mssv'] ?? '');
      sheetObject
          .cell(CellIndex.indexByColumnRow(columnIndex: 2, rowIndex: row))
          .value = TextCellValue(student['ho_ten'] ?? '');
      sheetObject
              .cell(CellIndex.indexByColumnRow(columnIndex: 3, rowIndex: row))
              .value =
          TextCellValue(student['trang_thai'] == 'Co mat' ? 'Có mặt' : 'Vắng');
      sheetObject
          .cell(CellIndex.indexByColumnRow(columnIndex: 4, rowIndex: row))
          .value = TextCellValue(student['thoi_gian'] ?? '');
    }

    var fileBytes = excel.save();
    if (fileBytes == null) return;

    final String fileName =
        'Diem_danh_${tenLop.replaceAll(' ', '_')}_${DateTime.now().millisecondsSinceEpoch}.xlsx';
    final directory = await getApplicationDocumentsDirectory();
    final String filePath = '${directory.path}/$fileName';

    final file = File(filePath);
    await file.create(recursive: true);
    await file.writeAsBytes(fileBytes);

    await Share.shareXFiles([XFile(filePath)],
        text: 'Báo cáo điểm danh $tenLop');
  }
}
