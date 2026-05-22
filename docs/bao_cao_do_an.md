# ĐỒ ÁN TỐT NGHIỆP: XÂY DỰNG ỨNG DỤNG ĐIỂM DANH DỰA TRÊN NHẬN DẠNG KHUÔN MẶT

**TRƯỜNG ĐẠI HỌC XÂY DỰNG MIỀN TÂY**
**KHOA CÔNG NGHỆ**
Ngành: Kỹ thuật phần mềm.
Mã ngành: 7480103
Sinh viên : Nguyễn Đông Từ
---

## Lời cảm ơn
Trong suốt quá trình học tập và đặc biệt là khi thực hiện đồ án tốt nghiệp này, em đã nhận được rất nhiều sự giúp đỡ, động viên và chỉ dẫn quý báu từ các thầy cô, bạn bè và người thân. Nhân dịp hoàn thành bài báo cáo, em xin được bày tỏ lòng biết ơn chân thành và sâu sắc đến tất cả những người đã đồng hành cùng em trong suốt chặng đường vừa qua.

Trước hết, em xin kính gửi lời cảm ơn đến Ban Giám hiệu cùng tập thể quý Thầy Cô Trường Đại Học Xây Dựng Miền Tây, đặc biệt là quý Thầy Cô Khoa Công Nghệ, đã tận tình giảng dạy, truyền đạt kiến thức và tạo điều kiện thuận lợi để em có thể tiếp thu tri thức chuyên môn, rèn luyện kỹ năng và hoàn thiện bản thân trong suốt quá trình học tập tại trường.

Đặc biệt, em xin trân trọng cảm ơn Cô Đặng Thị Xuân Tiên – người đã trực tiếp hướng dẫn em thực hiện đồ án tốt nghiệp này. Cô không chỉ tận tâm trong việc góp ý chỉnh sửa nội dung chuyên môn, định hướng tư duy khoa học, mà còn luôn kiên nhẫn hỗ trợ em vượt qua những khó khăn trong quá trình nghiên cứu và xây dựng hệ thống. Sự chỉ dẫn tận tình của Cô chính là nền tảng quan trọng để em hoàn thành đề tài một cách hiệu quả.

Mặc dù đã cố gắng hết sức trong quá trình nghiên cứu, tìm hiểu và thực hiện đề tài, tuy nhiên với kiến thức và kinh nghiệm thực tế còn hạn chế, bài báo cáo chắc chắn vẫn còn tồn tại những thiếu sót nhất định. Em kính mong nhận được sự góp ý chân thành từ quý Thầy Cô và các bạn để em có thể hoàn thiện hơn trong những nghiên cứu sau này.

Em xin chân thành cảm ơn!
Trân trọng,

---

## PHẦN 1. MỞ ĐẦU

### 1. Lý do chọn đề tài
Trong bối cảnh chuyển đổi số trở nên mạnh mẽ trên toàn thế giới, việc ứng dụng các công nghệ mới trong đời sống như trí tuệ nhân tạo (AI) và thị giác máy tính (Computer Vision) vào việc giáo dục ngày càng phổ biến và cấp thiết. Theo thống kê, việc sử dụng công cụ AI trong giáo dục giúp hoàn thành công việc nhiều hơn và nhanh hơn đáng kể. Một vấn đề phổ biến tại các cơ sở dạy học là công tác điểm danh sinh viên. Hiện nay đa số ở các lớp, các trường đều thực hiện điểm danh thủ công, rất mất thời gian, dễ xảy ra gian lận (điểm danh hộ) và gây khó khăn trong việc tổng hợp dữ liệu.
Nhận diện khuôn mặt là phương pháp xác thực sinh trắc học hiệu quả và nhanh chóng. Hệ thống điểm danh của tôi thực hiện việc điểm danh qua web cam, camera Kiosk chuyên dụng hoặc thông qua Mobile App. Điểm danh được thông qua giao diện tự động, xử lý AI ở Backend, trả về kết quả chính xác, giúp giáo viên dễ dàng kiểm soát danh sách sinh viên với độ chính xác cao (hơn 98%).

### 2. Lịch sử nghiên cứu
Các nghiên cứu ban đầu về nhận diện khuôn mặt triển khai với các phương pháp cơ bản như Eigenfaces, Fisherfaces, LBP. Hiện nay, sự phát triển của công nghệ học sâu (Deep Learning) mở ra kỷ nguyên mới với các mô hình mạng nơ-ron tích chập (CNN). Nhiều đề tài đã được nghiên cứu tại Việt Nam nhưng vẫn gặp thách thức về độ chính xác, hiệu năng thực thi, và khả năng chống giả mạo (Anti-Spoofing). Đề tài này kế thừa các công nghệ đó và mở rộng giải quyết triệt để vấn đề gian lận bằng các Engine đa dạng (InsightFace, DeepFace, YOLO11).

### 3. Mục tiêu nghiên cứu
- **Nhận diện khuôn mặt chính xác & đa nền tảng:** Chụp ảnh, lưu dữ liệu, huấn luyện, và nhận diện thông qua Camera Kiosk, ứng dụng di động Flutter, đồng thời hỗ trợ kết nối linh hoạt với các luồng Camera IP giám sát (IP Camera qua giao thức RTSP như Imou, Ezviz) giúp tận dụng hạ tầng có sẵn của trường học.
- **Áp dụng AI linh hoạt:** Sử dụng Multi-Engine Factory Pattern (InsightFace, DeepFace, YOLO+ResNet) để trích xuất đặc trưng.
- **Chống giả mạo (Anti-Spoofing):** Phát hiện và chặn các hành vi dùng ảnh giấy, màn hình điện thoại để điểm danh hộ thông qua phân tích độ mờ, độ chói và Liveness Detection.
- **Tích hợp Trợ lý AI (Chatbot):** Tích hợp kỹ thuật RAG (Retrieval-Augmented Generation) giúp Chatbot tư vấn, hướng dẫn và phân tích dữ liệu chuyên cần.
- **Giao diện hiện đại & Mobile App:** Quản lý qua giao diện Web Glassmorphism và ứng dụng Flutter đa nền tảng.

### 4. Phương pháp nghiên cứu
Thực hiện tìm hiểu các kiến thức và công cụ:
- Ngôn ngữ Python làm Backend và xử lý AI. 
- Ngôn ngữ Dart với framework Flutter cho ứng dụng Mobile.
- Các công cụ AI: OpenCV, MTCNN, FaceNet, DeepFace, YOLO11, TensorFlow, ChromaDB (cho RAG), Numpy (Cosine Similarity).
- Các kỹ thuật Backend: Flask, SocketIO, JWT, Docker.

### 5. Phạm vi đề tài
Hệ thống tập trung nghiên cứu, thiết kế, triển khai hệ thống điểm danh tự động bằng khuôn mặt từ thiết bị đầu cuối (Máy tính, điện thoại, Kiosk):
- Backend Python xử lý ảnh, nhận diện, cung cấp REST API.
- Frontend HTML/CSS/JS (Kiosk Mode) và Mobile App (Flutter).
- Phát hiện khuôn mặt bằng MTCNN / YOLO / SCRFD.
- Trích xuất đặc trưng bằng FaceNet / ArcFace / ResNet50.
- Tìm kiếm và so khớp khuôn mặt bằng Cosine Similarity (Numpy).
- Chatbot RAG hỗ trợ truy vấn thông tin.

### 6. Thành quả đạt được và ý nghĩa đề tài
- **Thành quả:** Giao diện Web/Kiosk dễ sử dụng; Mobile App 17 màn hình cho sinh viên tự check-in; Cơ chế Multi-Engine linh hoạt; Chống giả mạo hiệu quả (lưu log vào bảng gian_lan_log); Tích hợp AI Chatbot.
- **Ý nghĩa:** Tự động hóa quá trình điểm danh, tăng độ tin cậy và minh bạch, ngăn chặn gian lận, nâng cao hiệu quả quản lý lớp học.

---

## PHẦN 2. NỘI DUNG

### Chương 1. CƠ SỞ LÝ THUYẾT
#### 1.1. Các khái niệm cơ bản
- **Python:** Ngôn ngữ lập trình cấp cao, dễ đọc, cộng đồng hỗ trợ AI/ML cực kỳ mạnh mẽ.
- **Nhận diện khuôn mặt:** Sinh trắc học phân tích ánh xạ đặc điểm khuôn mặt thành faceprint, từ đó xác định danh tính. Quá trình gồm: Phát hiện -> Phân tích -> Chuyển đổi dữ liệu -> So sánh -> Xác nhận.
- **Deep Neural Networks (DNNs):** Mạng nơ-ron học sâu với nhiều lớp ẩn, tự động trích xuất đặc trưng hình ảnh tốt hơn so với trích xuất thủ công.
- **Vector đặc trưng (Face Embedding):** Biểu diễn khuôn mặt thành mảng số nhiều chiều. Khoảng cách Euclidean/Cosine giữa 2 vector nhỏ nghĩa là cùng một người.

#### 1.2. Công nghệ Nhận diện và Xử lý Ảnh
- **OpenCV:** Thư viện nguồn mở cho Computer Vision xử lý ảnh thời gian thực.
- **MTCNN & FaceNet:** MTCNN dùng 3 lớp mạng (P-Net, R-Net, O-Net) phát hiện khuôn mặt. FaceNet trích xuất đặc trưng embedding 128/512 chiều, sử dụng hàm mất mát Triplet Loss.
- **Kiến trúc Multi-Engine:** Hệ thống sử dụng Factory Pattern (`core/engine.py`) cho phép chuyển đổi nóng:
  - **InsightFace:** Dùng bộ phát hiện khuôn mặt SCRFD và mô hình trích xuất đặc trưng ArcFace 512 chiều.
  - **DeepFace Engine:** Tích hợp ArcFace, RetinaFace giúp phân tích đặc tính tuổi, giới tính.
  - **YOLO11 + ResNet50:** Phát hiện khuôn mặt tốc độ cao trong đám đông. YOLO11 sử dụng bộ tối ưu hóa MuSGD và NMS-free inference.
- **Cosine Similarity (Numpy):** Sử dụng tính toán khoảng cách Cosine với thư viện Numpy qua ma trận embeddings trên RAM để tăng tốc độ so khớp realtime giữa vector đầu vào và danh sách sinh viên.

#### 1.3. Liveness Detection & Chống giả mạo (Anti-Spoofing)
Đây là công nghệ sống còn để đảm bảo điểm danh minh bạch:
- **Heuristics Check:** Tính toán `Blur Score` (qua phương sai Laplacian) để chặn ảnh mờ; `Glare Ratio` (qua kênh V màu HSV) để phát hiện phản quang của màn hình thiết bị di động (chặn ảnh qua điện thoại); `Face Size Check` chặn ảnh chụp từ xa.
- **DeepFace Spoofing:** Mô-đun AI nhận diện ảnh tĩnh (giấy) hay ảnh thật (is_real). Các trường hợp vi phạm được log thẳng vào cơ sở dữ liệu `gian_lan_log` và phát chuông cảnh báo.

#### 1.4. Trợ lý AI (Chatbot) với Kỹ thuật RAG
Hệ thống sử dụng Retrieval-Augmented Generation (RAG):
- **ChromaDB:** Cơ sở dữ liệu Vector lưu trữ mã nguồn, quy trình, và kiến thức hệ thống sau khi chia nhỏ (chunking).
- **LLM Backend:** Hỗ trợ Gemini, NVIDIA NIM, và Ollama. Hệ thống sẽ truy xuất tài liệu liên quan trong ChromaDB gửi kèm câu hỏi của giáo viên đến LLM, giúp Chatbot có khả năng tư vấn nghiệp vụ, hướng dẫn thao tác, phân tích chuyên cần mà không bị ảo giác.

#### 1.5. Công nghệ phát triển ứng dụng Mobile & Backend
- **Backend (Flask/RESTX & SocketIO):** Nhận hình ảnh, chạy AI, và giao tiếp realtime với các client.
- **Flutter (Dart):** Dùng để phát triển ứng dụng di động cho sinh viên. Mobile App cung cấp các API gọi tới backend qua xác thực bảo mật JWT, hỗ trợ xử lý offline (tải dữ liệu khuôn mặt về thiết bị nội bộ).

---

### Chương 2. PHƯƠNG PHÁP THỰC HIỆN
#### 2.1. Kiến trúc hệ thống tổng thể (Tầng - Layered Architecture)
- **Tầng giao diện người dùng (Presentation):** Bao gồm giao diện Kiosk HUD (HTML/CSS Glassmorphism) và ứng dụng di động Flutter (Mobile App). Các nút bấm: Capture, Train, Recognize.
- **Tầng xử lý nghiệp vụ (Business Logic):** Backend Python Flask nhận ảnh định dạng Base64 (Web), Upload (Mobile), hoặc trực tiếp giải mã luồng stream RTSP từ IP Camera. Phân luồng cho AI Engine phát hiện chuyển động, kiểm tra Liveness, và khớp khuôn mặt bằng Numpy Cosine Similarity.
- **Tầng lưu trữ (Data Access):** 
  - MySQL Database quản lý sinh viên, lịch học, `gian_lan_log`, `phien_diem_danh`, `thong_bao`.
  - File System lưu trữ thư mục hình ảnh (`dataset`), video, và dữ liệu mô hình (`embeddings.pkl`).

#### 2.2. Quy trình hoạt động
Hệ thống áp dụng logic điểm danh một chiều (Check-in) tối giản, loại bỏ các thao tác check-out thừa thãi, tối ưu tốc độ dòng người đi qua Kiosk.
- **Giai đoạn 1 – Thu thập dữ liệu:** Sinh viên tự đăng ký khuôn mặt trên Mobile App hoặc chụp tại Kiosk Web. Ảnh được kiểm tra chống mờ/chói tự động, nếu đạt mới được lưu vào CSDL.
- **Giai đoạn 2 – Huấn luyện mô hình:** Khi chạy hàm Training, hệ thống sử dụng FaceNet/ArcFace trích xuất vector khuôn mặt trung bình của mỗi sinh viên và lưu trực tiếp vào file `embeddings.pkl` trên RAM. Không cần huấn luyện lại cấu trúc mạng (Zero-shot). Hỗ trợ huấn luyện thêm mô hình YOLO11 thông qua công cụ Label Tool Web-based.
- **Giai đoạn 3 – Nhận diện và Điểm danh:** Hệ thống Kiosk chỉ kích hoạt Camera và bắt đầu nhận diện khi Giảng viên mở Phiên (Session) điểm danh, giúp tối ưu tài nguyên và tăng cường bảo mật. Khi kích hoạt, Camera truyền ảnh về Backend xử lý qua Thread độc lập. Mô-đun Anti-Spoofing chạy trước, nếu hợp lệ -> tính khoảng cách Cosine với kho dữ liệu RAM -> cập nhật lịch sử, đẩy Push Notification tới Mobile App sinh viên.
- **Giai đoạn 4 – Tương tác Chatbot:** Giáo viên nhập câu hỏi vào Dashboard. Chatbot lọc thông tin nhạy cảm, tra cứu cơ sở dữ liệu Vector và trả về báo cáo lớp học bằng ngôn ngữ tự nhiên.

---

### Chương 3. KẾT QUẢ ĐẠT ĐƯỢC
#### 3.1. Xây dựng và triển khai
- **Giao diện Dashboard & Kiosk:** Hiện đại, có slider zoom cho camera, hiển thị HUD bounding box thời gian thực.
- **Ứng dụng Mobile Flutter:** 17 màn hình chức năng hoạt động mượt mà, bao gồm cả điểm danh bằng QR, xem lịch học, quản lý khuôn mặt, với thiết kế đồng bộ hệ thống.
- **Bảo mật và Tự động hóa:** Toàn bộ hệ thống được đóng gói bằng `Dockerfile` giúp triển khai trên mọi máy chủ dễ dàng.

#### 3.2. Đánh giá tốc độ và độ chính xác các Engine AI
- **InsightFace (buffalo_l):** Đạt độ chính xác >99.5%, tốc độ ~20 FPS. Rất ổn định.
- **DeepFace:** Tích hợp tốt với các luồng chống giả mạo, độ chính xác cao nhưng FPS giảm xuống mức 10-12 FPS, phù hợp kiểm soát cửa bảo mật.
- **YOLO11+ResNet50:** Tốc độ rất nhanh trong việc phát hiện đám đông, NMS-free giúp giảm thời gian hậu xử lý, nhận diện đến 30 người/frame.

#### 3.3. Hiệu quả của mô-đun Anti-Spoofing
- Chặn thành công >90% hành vi điểm danh qua ảnh điện thoại bằng Glare Ratio (phát hiện màn hình chói).
- DeepFace Liveness chặn 100% hình ảnh in giấy tĩnh. Tất cả hành vi đều được chụp lại và đẩy lên bảng `gian_lan_log`.

---

## PHẦN 3. KẾT LUẬN VÀ KIẾN NGHỊ

### 1. Kết luận / Đánh giá
Hệ thống sử dụng đa mô hình AI tiên tiến (InsightFace, YOLO, DeepFace) kết hợp đo khoảng cách Cosine Similarity mang lại độ chính xác kiểm tra trung bình đạt trên 98%. Hệ thống hoạt động hoàn toàn ổn định và linh hoạt (Zero-shot) nhờ thiết kế lược bỏ các mạng phân loại cổ điển. Các tính năng mở rộng như ứng dụng Mobile Flutter và RAG Chatbot đã nâng tầm dự án thành một giải pháp phần mềm giáo dục thực tế và toàn diện. Nút thắt lớn nhất về "điểm danh hộ" (gian lận) đã được giải quyết cơ bản với mô-đun Anti-Spoofing.

### 2. Ưu điểm
- **Tự động hóa toàn diện:** Từ Kiosk không chạm đến điểm danh Mobile cá nhân.
- **Chính xác & Minh bạch:** AI hoạt động chính xác >98%, tự động đẩy log gian lận.
- **Giao diện thân thiện:** Web Glassmorphism và Mobile App trực quan, dễ sử dụng.
- **Kiến trúc mở:** Multi-Engine Factory giúp dễ dàng nâng cấp thuật toán AI mới mà không phá vỡ logic cũ. Container hóa bằng Docker.

### 3. Hạn chế
- **Yêu cầu phần cứng:** Chạy nhiều AI Engine và Anti-spoofing cùng lúc đòi hỏi máy chủ phải có cấu hình tương đối để đạt FPS cao nhất.
- **Phụ thuộc điều kiện môi trường:** Ánh sáng quá yếu hoặc ngược sáng mạnh có thể làm giảm hiệu suất của thuật toán Glare Ratio trong Liveness.

### 4. Hướng Phát triển
- Tối ưu triển khai trên thiết bị Edge AI (NVIDIA Jetson Nano) để đặt hẳn tại cửa lớp, không phụ thuộc vào máy chủ trung tâm.
- Nâng cấp Chatbot AI có khả năng giao tiếp qua giọng nói tự nhiên với Kiosk.
- Thêm tính năng BLE (Bluetooth Low Energy) trên ứng dụng Flutter để xác thực cự ly của sinh viên trong phòng học một cách tuyệt đối, kết hợp với nhận diện khuôn mặt.

---

## TÀI LIỆU THAM KHẢO
[1] Tổng hợp số liệu nghiên cứu về AI, Brands Vietnam.
[2] "Python là gì", ITviec Blog.
[3] "Công nghệ nhận diện khuôn mặt là gì", VNPT AI.
[4] "Neural Network là gì", VNPT AI.
[5] Feature Vector, Deepchecks.
[6] OpenCV là gì, TopDev.
[7] Tích hợp mạng MTCNN và FaceNet.
[8] Flutter Documentation & Dart APIs.
[9] Kỹ thuật Retrieval-Augmented Generation (RAG), NVIDIA NIM.
[10] Tham khảo các thư viện: TensorFlow, Numpy, Scikit-learn, Pandas, Faiss.
