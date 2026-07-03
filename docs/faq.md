# Câu hỏi thường gặp & Gỡ rối kỹ thuật (FAQ)

Tài liệu này tập hợp các kiến thức xử lý sự cố và thông tin chuyên sâu để giúp AI hoặc quản trị viên hệ thống hiểu rõ tường tận cách MTUFace hoạt động.

## 1. Về AI Chatbot & LLM Backend

**Hỏi: Hệ thống đang dùng loại Bot nào? Làm sao đổi sang bot miễn phí?**
- Hệ thống hỗ trợ 3 loại AI: `gemini` (Google), `nvidia`, và `lmstudio` (Chạy Offline 100%).
- Để thay đổi, hãy sửa file `.env` ở thư mục gốc: `AI_CHATBOT_LLM=lmstudio`. 
- Nếu chọn `lmstudio`, bạn phải đảm bảo LM Studio đang bật Local Server ở địa chỉ `http://127.0.0.1:1234`.

**Hỏi: Tính năng `/search` hoạt động thế nào? Local AI có tìm được mạng không?**
- Có! Bất kể dùng Gemini hay LM Studio, chỉ cần người dùng gõ `/search abc`, hệ thống backend (Python) sẽ tự động dùng thư viện `duckduckgo-search` để cào dữ liệu từ Internet.
- Sau đó, thông tin cào được sẽ nạp vào bộ não của Bot để Bot trả lời. Tính năng này miễn phí 100% và chạy được cả trên mạng cục bộ (miễn là máy chủ có mạng).

**Hỏi: Kho tri thức (RAG) bị sai hoặc Bot trả lời tầm bậy thì làm sao?**
- Rất đơn giản! Chỉ cần mở file `.md` (trong thư mục `docs/`), sửa lại nội dung bị sai cho đúng. Sau đó vào trang Web Admin -> Bấm **Cập nhật KB** (Nút có hình mũi tên xoay vòng).
- Lúc này, `knowledge_builder.py` sẽ xoá não cũ của Bot và nạp toàn bộ kiến thức mới vào (sử dụng thư viện ChromaDB).

## 2. Về Thuật toán AI Nhận diện (Computer Vision)

**Hỏi: Thuật toán nhận diện đang dùng là gì? Làm sao phân biệt được 2 khuôn mặt?**
- Bước 1: Dùng YOLO / RetinaFace để dò tìm vùng chứa khuôn mặt (Face Detection).
- Bước 2: Truyền vùng mặt đó qua mạng học sâu `ArcFace` / `InsightFace` (Sử dụng ONNX Runtime) để trích xuất ra một đoạn mã 512 con số (gọi là Face Embedding / Face Vector).
- Bước 3: Đo khoảng cách Cosine Distance giữa vector của người đang đứng trước camera và vector gốc lưu trong database. Khoảng cách càng nhỏ (dưới ngưỡng 0.45) thì tỉ lệ 2 người là 1 càng cao.

**Hỏi: Máy chấm công không nhận ra mặt tôi (hoặc nhận nhầm sang người khác)?**
- Xảy ra khi: Ánh sáng quá yếu, ảnh mẫu bị mờ, hoặc góc mặt quá nghiêng.
- Cách xử lý: 
  - Khuyên sinh viên chụp lại 5 tấm ảnh huấn luyện gốc thật rõ nét.
  - Sửa biến số `THRESHOLD` (Ngưỡng khoảng cách) trong thư mục `core/`. Nếu nhận nhầm quá nhiều, hạ ngưỡng xuống `0.35` (chặt chẽ hơn). Nếu khó nhận, nâng lên `0.55` (thoải mái hơn).

**Hỏi: Có chống gian lận (Anti-spoofing) lấy điện thoại giơ lên điểm danh không?**
- Hệ thống hỗ trợ 2 dạng: 
  - Passive Liveness: Dùng model AI (như FAS - Face Anti Spoofing) để dự đoán bề mặt phẳng của điện thoại hay độ sâu khuôn mặt thật.
  - Active Liveness: Yêu cầu sinh viên chớp mắt / lắc đầu để xác minh. (Tùy chọn thiết lập).
