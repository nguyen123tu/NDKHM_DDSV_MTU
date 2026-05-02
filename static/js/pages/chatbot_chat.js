const messagesEl = document.getElementById('chatMessages');
const inputEl = document.getElementById('chatInput');
const typingEl = document.getElementById('typingIndicator');
const suggestionsEl = document.getElementById('suggestions');
let isLoading = false;

// Auto-resize textarea
inputEl.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 120) + 'px';
});

function sendMessage() {
    const text = inputEl.value.trim();
    if (!text || isLoading) return;
    
    addMessage(text, 'user');
    inputEl.value = ''; inputEl.style.height = 'auto';
    suggestionsEl.style.display = 'none';
    setLoading(true);

    fetch('/chatbot/ask', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({question: text})
    })
    .then(r => r.json())
    .then(data => {
        setLoading(false);
        addMessage(data.answer, 'bot', data.sources, data.duration_ms);
    })
    .catch(err => {
        setLoading(false);
        addMessage('❌ Lỗi kết nối: ' + err.message, 'bot');
    });
}

function addMessage(text, role, sources, duration) {
    const div = document.createElement('div');
    div.className = 'msg ' + role;
    
    let html = '<div class="bubble">' + (role === 'bot' ? marked.parse(text) : escapeHtml(text)) + '</div>';
    
    if (role === 'bot' && duration) {
        html += '<div class="meta">⏱ ' + duration + 'ms</div>';
    }
    if (sources && sources.length > 0) {
        const srcList = [...new Set(sources.map(s => s.file))].join(', ');
        html += '<div class="sources">📚 Nguồn: ' + srcList + '</div>';
    }
    
    div.innerHTML = html;
    messagesEl.insertBefore(div, typingEl);
    messagesEl.scrollTop = messagesEl.scrollHeight;
}

function setLoading(v) {
    isLoading = v;
    typingEl.style.display = v ? 'block' : 'none';
    document.getElementById('btnSend').disabled = v;
    if (v) messagesEl.scrollTop = messagesEl.scrollHeight;
}

function askSuggested(el) { inputEl.value = el.textContent; sendMessage(); }

function clearChat() {
    fetch('/chatbot/clear', {method:'POST'}).then(() => {
        const msgs = messagesEl.querySelectorAll('.msg:not(.typing-indicator)');
        msgs.forEach((m, i) => { if(i > 0) m.remove(); });
        suggestionsEl.style.display = 'flex';
    });
}

function buildKnowledge() {
    const btn = document.getElementById('btnBuild');
    btn.disabled = true; btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Đang xây dựng...';
    
    fetch('/chatbot/build-knowledge', {method:'POST'});
    
    document.getElementById('kbProgress').style.display = 'block';
    const evtSrc = new EventSource('/chatbot/knowledge-progress');
    evtSrc.onmessage = function(e) {
        const d = JSON.parse(e.data);
        document.getElementById('kbProgressBar').style.width = (d.progress * 100) + '%';
        document.querySelector('#kbBar span').textContent = d.message;
        
        if (d.status === 'done' || d.status === 'error') {
            evtSrc.close(); btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-database"></i> <span class="d-none d-md-inline">Cập nhật KB</span>';
            if (d.status === 'done') {
                document.getElementById('kbBar').className = 'kb-bar ready';
                document.getElementById('kbProgress').style.display = 'none';
            }
            setTimeout(() => location.reload(), 1500);
        }
    };
    evtSrc.onerror = function() { evtSrc.close(); btn.disabled = false; btn.innerHTML = '<i class="fas fa-database"></i> Cập nhật KB'; };
}

function escapeHtml(t) { const d = document.createElement('div'); d.textContent = t; return d.innerHTML; }

// Focus input on load
inputEl.focus();