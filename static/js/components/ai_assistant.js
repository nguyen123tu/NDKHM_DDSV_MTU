/**
 * MTU AI Assistant — Smart Chatbot Widget
 * Trợ lý AI thông minh cho hệ thống điểm danh
 */

(function () {
    'use strict';

    // ═══════════════════════════════════════════════════════
    // Knowledge Base (Câu hỏi - Trả lời)
    // ═══════════════════════════════════════════════════════
    const KB = [
        {
            keywords: ['xin chào', 'hello', 'hi', 'chào', 'hey'],
            answer: '👋 Xin chào! Tôi là **MTU Assistant** — trợ lý AI của hệ thống Điểm Danh Khuôn Mặt. Tôi có thể giúp bạn về:\n\n• Hướng dẫn sử dụng hệ thống\n• Giải đáp thắc mắc kỹ thuật\n• Thống kê và báo cáo\n\nBạn cần hỗ trợ gì?'
        },
        {
            keywords: ['điểm danh', 'attendance', 'cách điểm danh', 'check in'],
            answer: '📸 **Hướng dẫn Điểm Danh:**\n\n1. Vào mục **Ghi nhận ra/vào** trên sidebar\n2. Chọn camera và lớp học cần điểm danh\n3. Hệ thống sẽ tự động nhận diện khuôn mặt\n4. Kết quả được ghi nhận ngay lập tức\n\n💡 *Sinh viên cũng có thể tự điểm danh qua trang Public Selfcheck!*'
        },
        {
            keywords: ['thêm sinh viên', 'add student', 'tạo sinh viên', 'nhập sinh viên'],
            answer: '👨‍🎓 **Thêm Sinh Viên mới:**\n\n1. Vào **Quản lý sinh viên** → Nhấn "Thêm mới"\n2. Điền thông tin: MSSV, Họ tên, Lớp\n3. Upload ảnh khuôn mặt (tối thiểu 3 ảnh)\n4. Nhấn **Lưu** để hoàn tất\n\n⚠️ *Sau khi thêm, cần chạy **Training** để AI nhận diện được sinh viên mới!*'
        },
        {
            keywords: ['training', 'train', 'huấn luyện', 'đào tạo', 'học'],
            answer: '🧠 **Training Dữ Liệu AI:**\n\n1. Vào mục **Training Dữ Liệu** trên sidebar\n2. Kiểm tra số ảnh đã có trong database\n3. Nhấn **Bắt đầu Training**\n4. Chờ hệ thống xử lý (thường 1-5 phút)\n\n✅ *Mỗi lần thêm/xóa sinh viên đều cần Training lại để cập nhật model!*'
        },
        {
            keywords: ['kiosk', 'chế độ kiosk', 'kiosk mode', 'màn hình'],
            answer: '🖥️ **Kiosk Mode:**\n\nĐây là chế độ hiển thị toàn màn hình, phù hợp đặt tại cửa lớp để sinh viên tự điểm danh.\n\n• Vào **Kiosk Mode** trên sidebar\n• Camera tự động bật và quét khuôn mặt\n• Hiển thị thông tin SV ngay khi nhận diện\n• Ghi log tự động vào database'
        },
        {
            keywords: ['lớp', 'class', 'quản lý lớp', 'tạo lớp'],
            answer: '🏫 **Quản lý Lớp Học:**\n\n• Vào **Quản lý lớp học** trên sidebar\n• Có thể tạo mới, sửa, xóa lớp\n• Gán sinh viên vào lớp\n• Xem thống kê điểm danh theo lớp\n\n📊 *Mỗi lớp có mã riêng và danh sách sinh viên!*'
        },
        {
            keywords: ['lỗi', 'error', 'bug', 'không', 'hỏng', 'sai', 'fail'],
            answer: '🔧 **Xử lý sự cố thường gặp:**\n\n1. **Camera không mở:** Kiểm tra quyền truy cập camera trong trình duyệt\n2. **Không nhận diện được:** Chạy lại Training và kiểm tra ảnh database\n3. **Trang bị trắng:** Xóa cache trình duyệt (Ctrl+Shift+R)\n4. **Lỗi kết nối DB:** Kiểm tra MySQL có đang chạy không\n\n🆘 *Nếu vẫn lỗi, liên hệ admin hệ thống!*'
        },
        {
            keywords: ['thống kê', 'báo cáo', 'report', 'statistics', 'dashboard'],
            answer: '📊 **Thống kê & Báo cáo:**\n\nTrang chủ Dashboard hiển thị:\n• Tổng số sinh viên đã đăng ký\n• Số lượt điểm danh hôm nay\n• Biểu đồ xu hướng theo ngày\n• Danh sách điểm danh gần nhất\n\n📈 *Dữ liệu được cập nhật real-time!*'
        },
        {
            keywords: ['công nghệ', 'technology', 'tech', 'ai', 'model', 'framework'],
            answer: '⚡ **Công nghệ sử dụng:**\n\n🔹 **Backend:** Flask (Python)\n🔹 **AI Engine:** InsightFace (ArcFace + MTCNN)\n🔹 **Database:** MySQL\n🔹 **Frontend:** Bootstrap 5, Chart.js\n🔹 **Mobile:** Flutter\n🔹 **Real-time:** Socket.IO\n\n🎯 *Độ chính xác nhận diện: ~99.2%*'
        },
        {
            keywords: ['duyệt', 'pending', 'khuôn mặt chờ', 'xác nhận'],
            answer: '✅ **Duyệt Khuôn Mặt:**\n\nKhi sinh viên tự đăng ký ảnh mới:\n1. Vào **Duyệt khuôn mặt** trên sidebar\n2. Xem ảnh chờ duyệt\n3. Chấp nhận hoặc từ chối từng ảnh\n4. Ảnh được duyệt sẽ tự thêm vào database\n\n💡 *Nên kiểm tra kỹ để đảm bảo chất lượng ảnh!*'
        },
        {
            keywords: ['giúp', 'help', 'hỗ trợ', 'support', 'gì', 'làm được gì'],
            answer: '🤖 Tôi có thể hỗ trợ bạn:\n\n📌 **Hướng dẫn sử dụng** — Cách dùng từng tính năng\n📌 **Xử lý lỗi** — Giải quyết sự cố thường gặp\n📌 **Thông tin kỹ thuật** — Công nghệ AI đang sử dụng\n📌 **Thống kê** — Xem báo cáo điểm danh\n\nHãy hỏi tôi bất cứ điều gì! 😊'
        }
    ];

    const GREETINGS = [
        'Chào bạn! 👋 Tôi là **MTU Assistant**, trợ lý AI điểm danh khuôn mặt. Hỏi tôi bất cứ điều gì về hệ thống nhé!',
    ];

    const FALLBACKS = [
        '🤔 Mình chưa hiểu rõ câu hỏi. Bạn thử hỏi về: *điểm danh, training, quản lý sinh viên, kiosk mode* nhé!',
        '💭 Hmm, tôi không chắc về câu hỏi này. Hãy thử các gợi ý bên dưới hoặc hỏi cách khác nhé!',
        '🧐 Xin lỗi, tôi chưa có thông tin về vấn đề này. Bạn có thể hỏi về tính năng hoặc cách sử dụng hệ thống!',
    ];

    // ═══════════════════════════════════════════════════════
    // AI Logic
    // ═══════════════════════════════════════════════════════
    function findAnswer(input) {
        const q = input.toLowerCase().trim();
        let bestMatch = null;
        let bestScore = 0;

        for (const item of KB) {
            let score = 0;
            for (const kw of item.keywords) {
                if (q.includes(kw)) {
                    score += kw.length; // longer match = better
                }
            }
            if (score > bestScore) {
                bestScore = score;
                bestMatch = item;
            }
        }

        if (bestMatch && bestScore > 0) {
            return bestMatch.answer;
        }
        return FALLBACKS[Math.floor(Math.random() * FALLBACKS.length)];
    }

    // Simple markdown-lite renderer
    function renderMarkdown(text) {
        return text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n/g, '<br>');
    }

    // ═══════════════════════════════════════════════════════
    // DOM Builder
    // ═══════════════════════════════════════════════════════
    function buildWidget() {
        // FAB
        const fab = document.createElement('button');
        fab.className = 'ai-fab';
        fab.id = 'aiFab';
        fab.innerHTML = '<span class="fab-icon"><i class="fas fa-robot"></i></span><span class="fab-dot"></span>';

        // Chat Window
        const win = document.createElement('div');
        win.className = 'ai-chat-window';
        win.id = 'aiChatWindow';
        win.innerHTML = `
            <div class="ai-chat-header">
                <div class="ai-avatar"><i class="fas fa-robot"></i></div>
                <div class="ai-header-info">
                    <h6>MTU Assistant</h6>
                    <span>Luôn sẵn sàng hỗ trợ</span>
                </div>
            </div>
            <div class="ai-chat-body" id="aiChatBody"></div>
            <div class="ai-suggestions" id="aiSuggestions">
                <div class="ai-chip" data-q="Hướng dẫn điểm danh"><i class="fas fa-camera"></i>Điểm danh</div>
                <div class="ai-chip" data-q="Cách thêm sinh viên"><i class="fas fa-user-plus"></i>Thêm SV</div>
                <div class="ai-chip" data-q="Cách training AI"><i class="fas fa-brain"></i>Training</div>
                <div class="ai-chip" data-q="Công nghệ AI"><i class="fas fa-microchip"></i>Tech Stack</div>
            </div>
            <div class="ai-chat-footer">
                <input type="text" class="ai-chat-input form-control" id="aiInput" placeholder="Hỏi tôi bất cứ điều gì..." autocomplete="off">
                <button class="ai-send-btn" id="aiSendBtn"><i class="fas fa-paper-plane"></i></button>
            </div>
        `;

        document.body.appendChild(win);
        document.body.appendChild(fab);
    }

    // ═══════════════════════════════════════════════════════
    // Chat Functions
    // ═══════════════════════════════════════════════════════
    function addMessage(text, type) {
        const body = document.getElementById('aiChatBody');
        const msg = document.createElement('div');
        msg.className = `ai-msg ${type}`;

        const avatarIcon = type === 'bot' ? 'fa-robot' : 'fa-user';
        msg.innerHTML = `
            <div class="ai-msg-avatar"><i class="fas ${avatarIcon}"></i></div>
            <div class="ai-msg-bubble">${renderMarkdown(text)}</div>
        `;

        body.appendChild(msg);
        body.scrollTop = body.scrollHeight;
    }

    function showTyping() {
        const body = document.getElementById('aiChatBody');
        const typing = document.createElement('div');
        typing.className = 'ai-msg bot';
        typing.id = 'aiTyping';
        typing.innerHTML = `
            <div class="ai-msg-avatar"><i class="fas fa-robot"></i></div>
            <div class="ai-msg-bubble ai-typing">
                <div class="ai-typing-dot"></div>
                <div class="ai-typing-dot"></div>
                <div class="ai-typing-dot"></div>
            </div>
        `;
        body.appendChild(typing);
        body.scrollTop = body.scrollHeight;
    }

    function hideTyping() {
        const t = document.getElementById('aiTyping');
        if (t) t.remove();
    }

    function handleSend() {
        const input = document.getElementById('aiInput');
        const text = input.value.trim();
        if (!text) return;

        addMessage(text, 'user');
        input.value = '';

        // Hide suggestions after first user message
        const suggestions = document.getElementById('aiSuggestions');
        if (suggestions) suggestions.style.display = 'none';

        // Show typing then answer
        showTyping();
        const delay = 600 + Math.random() * 800;
        setTimeout(() => {
            hideTyping();
            const answer = findAnswer(text);
            addMessage(answer, 'bot');
        }, delay);
    }

    // ═══════════════════════════════════════════════════════
    // Init
    // ═══════════════════════════════════════════════════════
    function init() {
        buildWidget();

        const fab = document.getElementById('aiFab');
        const win = document.getElementById('aiChatWindow');
        const input = document.getElementById('aiInput');
        const sendBtn = document.getElementById('aiSendBtn');
        let opened = false;

        // Toggle chat
        fab.addEventListener('click', () => {
            opened = !opened;
            fab.classList.toggle('active', opened);
            win.classList.toggle('open', opened);

            if (opened) {
                // First open — show greeting
                const body = document.getElementById('aiChatBody');
                if (body.children.length === 0) {
                    addMessage(GREETINGS[0], 'bot');
                }
                setTimeout(() => input.focus(), 400);
            }
        });

        // Send message
        sendBtn.addEventListener('click', handleSend);
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') handleSend();
        });

        // Suggestion chips
        document.querySelectorAll('.ai-chip').forEach(chip => {
            chip.addEventListener('click', () => {
                const q = chip.getAttribute('data-q');
                input.value = q;
                handleSend();
            });
        });

        // Close on Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && opened) {
                opened = false;
                fab.classList.remove('active');
                win.classList.remove('open');
            }
        });
    }

    // Run when DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
