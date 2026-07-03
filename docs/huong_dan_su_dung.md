# Hướng Dẫn Sử Dụng Hệ thống Điểm danh MTUFace

Chào mừng bạn đến với MTUFace! Đây là tài liệu hướng dẫn nhanh cách sử dụng các tính năng chính của hệ thống.

## 1. Web Admin (Quản trị viên)
Truy cập vào trang web với quyền Admin (Mặc định thường ở port 5000, `http://localhost:5000/admin`).

### 1.1 Khai báo sinh viên & Lớp học
- Chuyển sang tab **Lớp Học**, thêm các lớp mới.
- Chuyển sang tab **Sinh Viên**, ấn **Thêm Sinh Viên**. Bắt buộc nhập Tên và Mã Số Sinh Viên (MSSV).
- **Rất quan trọng:** Bạn cần tải lên ít nhất 1-3 bức ảnh rõ mặt (chụp thẳng, không đeo kính râm, không đội nón che khuất mặt) để AI có thể "nhớ" mặt sinh viên này. Hệ thống sẽ tự động rút trích đặc trưng khuôn mặt (Embedding) vào cơ sở dữ liệu.

### 1.2 Màn hình Live Attendance (Theo dõi điểm danh Real-time)
- Mở menu **Theo dõi điểm danh**.
- Tại đây, hệ thống sử dụng kết nối WebSockets (Socket.IO).
- Mỗi khi có sinh viên nào đi ngang qua Camera và quét mặt thành công trên App Mobile, thông tin của họ (tên, hình ảnh, thời gian) sẽ "nhảy" thẳng lên màn hình máy tính của giảng viên ngay lập tức mà không cần nhấn F5 (Tải lại trang).

## 2. Ứng dụng Di động (Mobile App - Flutter)
Giảng viên (hoặc bảo vệ/lớp trưởng) sử dụng điện thoại làm "Máy chấm công di động".

- Mở App, màn hình chính (Main Screen) sẽ là Camera đang quét liên tục.
- Yêu cầu sinh viên bước vào vùng xanh rực rỡ của camera.
- Máy sẽ nhấp nháy, nếu nhận diện trùng khớp khuôn mặt trong CSDL, máy sẽ kêu "Ting" và điểm danh thành công. Nếu không nhận ra, máy báo lỗi đỏ.

## 3. Sử Dụng Trợ lý AI Thông Minh (Chatbot)
Ở trang Web Admin hoặc Mobile, có một biểu tượng Robot để trò chuyện cùng AI chuyên gia của trường.

- **Tra cứu nội quy & Dữ liệu điểm danh**: 
  - Chat bình thường: "Chào bạn, hôm nay có mấy người vắng?" hoặc "Quy định cấm thi là vắng mấy buổi?"
  - AI sẽ lục lọi trí nhớ (từ các file Báo cáo, Nội quy) và dữ liệu thực của sinh viên để trả lời.
  - Sinh viên cũng có thể hỏi "Tôi là Nguyễn Văn A, tôi vắng mấy buổi rồi?" AI sẽ báo chính xác nhờ thông tin Realtime Context.
- **Tra cứu Internet ra bên ngoài (Duyệt Web)**:
  - Hãy gõ thêm lệnh `/search` vào đầu câu hỏi.
  - Ví dụ: `/search Thời tiết Vĩnh Long hôm nay thế nào?` hoặc `/search Tin tức hot nhất 24h qua`.
  - Lúc này, AI sẽ tạm quên dữ liệu nội bộ, tự động lướt web (DuckDuckGo) để bưng dữ liệu mới nhất về hầu hạ bạn!

## 4. Quản trị Kho tri thức cho AI (Dành cho Giảng Viên / Dev)
- Nếu thấy AI trả lời ngớ ngẩn, chưa đúng, hãy mở ổ đĩa thư mục chứa source code.
- Vào thư mục `docs/`, cập nhật nội dung các file văn bản (`.md`).
- Sau khi lưu file xong, trên giao diện chat của Web, bấm biểu tượng **Bánh Răng Cài Đặt**, chọn **"Cập nhật KB"**. AI sẽ học lại toàn bộ kiến thức mới!
