import 'dart:io';
import 'package:excel/excel.dart';
import 'package:path_provider/path_provider.dart';
import 'package:share_plus/share_plus.dart';
import 'package:flutter/foundation.dart' show kIsWeb;

/// Dịch vụ xuất báo cáo Excel cho Mobile.
/// Đã loại bỏ dart:html để có thể build APK Android thành công.
class ExportService {
  static Future<void> exportAttendanceToExcel(List<dynamic> history) async {
    if (kIsWeb) {
      // Trên Web, tính năng này tạm thời bị vô hiệu hóa để ưu tiên build APK.
      return;
    }

    var excel = Excel.createExcel();
    Sheet sheetObject = excel['Báo cáo điểm danh'];
    excel.delete('Sheet1');

    // Header style
    CellStyle headerStyle = CellStyle(
      backgroundColorHex: ExcelColor.fromHexString('#1B3A5C'),
      fontColorHex: ExcelColor.fromHexString('#FFFFFF'),
      bold: true,
      horizontalAlign: HorizontalAlign.Center,
    );

    // Thêm Tiêu đề cột
    List<String> headers = ["STT", "MSSV", "Họ và Tên", "Lớp", "Thời gian", "Trạng thái"];
    for (var i = 0; i < headers.length; i++) {
        var cell = sheetObject.cell(CellIndex.indexByColumnRow(columnIndex: i, rowIndex: 0));
        cell.value = TextCellValue(headers[i]);
        cell.cellStyle = headerStyle;
    }

    // Thêm Dữ liệu
    for (int i = 0; i < history.length; i++) {
      final record = history[i];
      int row = i + 1;
      
      sheetObject.cell(CellIndex.indexByColumnRow(columnIndex: 0, rowIndex: row)).value = IntCellValue(i + 1);
      sheetObject.cell(CellIndex.indexByColumnRow(columnIndex: 1, rowIndex: row)).value = TextCellValue(record.mssv);
      sheetObject.cell(CellIndex.indexByColumnRow(columnIndex: 2, rowIndex: row)).value = TextCellValue(record.hoTen);
      sheetObject.cell(CellIndex.indexByColumnRow(columnIndex: 3, rowIndex: row)).value = TextCellValue(record.maLop);
      sheetObject.cell(CellIndex.indexByColumnRow(columnIndex: 4, rowIndex: row)).value = TextCellValue(record.thoiGian);
      sheetObject.cell(CellIndex.indexByColumnRow(columnIndex: 5, rowIndex: row)).value = TextCellValue("Hợp lệ");
    }

    // Lưu và Chia sẻ file (Chỉ Mobile)
    var fileBytes = excel.save();
    if (fileBytes == null) return;

    final String fileName = 'Bao_cao_diem_danh_${DateTime.now().millisecondsSinceEpoch}.xlsx';
    final directory = await getApplicationDocumentsDirectory();
    final String filePath = '${directory.path}/$fileName';
    
    final file = File(filePath);
    await file.create(recursive: true);
    await file.writeAsBytes(fileBytes);

    // Mở hộp thoại chia sẻ file trên điện thoại
    await Share.shareXFiles([XFile(filePath)], text: 'Báo cáo điểm danh MTUFace');
  }
}
