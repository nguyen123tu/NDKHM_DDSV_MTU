/* chatbot_chat.js — Chat UI with sidebar history */
const messagesEl = document.getElementById('chatMessages');
const inputEl = document.getElementById('chatInput');
const typingEl = document.getElementById('typingIndicator');
const chatApp = document.getElementById('chatApp');
const sidebar = document.getElementById('chatSidebar');
let isLoading = false;

// --- Chat History (localStorage) ---
const CH = {
    KEY: 'mtu_chats',
    _d: null,
    load() { try { this._d = JSON.parse(localStorage.getItem(this.KEY)) || []; } catch { this._d = []; } return this._d; },
    save() { localStorage.setItem(this.KEY, JSON.stringify(this._d || [])); },
    all() { if (!this._d) this.load(); return this._d; },
    add(id, title) { if (!this._d) this.load(); this._d.unshift({ id, title, ts: Date.now(), msgs: [] }); this.save(); },
    rm(id) { if (!this._d) this.load(); this._d = this._d.filter(c => c.id !== id); this.save(); },
    clear() { this._d = []; this.save(); },
    get(id) { if (!this._d) this.load(); return this._d.find(c => c.id === id); },
    addMsg(id, role, text, sources, dur) {
        const c = this.get(id);
        if (!c) return;
        c.msgs.push({ role, text, sources, dur, t: Date.now() });
        if (role === 'user' && c.msgs.filter(m => m.role === 'user').length === 1)
            c.title = text.substring(0, 35) + (text.length > 35 ? '…' : '');
        this.save();
    }
};

let curId = null;
function genId() { return 'c_' + Date.now() + '_' + Math.random().toString(36).substr(2, 5); }

// --- Init ---
(function () {
    applyTheme(localStorage.getItem('chatTheme') || 'dark');
    const h = CH.all();
    if (h.length > 0) { curId = h[0].id; loadChat(curId); }
    else newChat(true);
    renderList();
    inputEl.addEventListener('input', function () { this.style.height = 'auto'; this.style.height = Math.min(this.scrollHeight, 120) + 'px'; });
    document.getElementById('btnSidebarToggle').addEventListener('click', () => sidebar.classList.toggle('collapsed'));
    document.getElementById('btnThemeToggle').addEventListener('click', toggleTheme);
    inputEl.focus();
})();

// --- Theme ---
function applyTheme(t) {
    chatApp.classList.toggle('light', t === 'light');
    document.getElementById('btnThemeToggle').innerHTML = t === 'light' ? '<i class="fas fa-sun"></i>' : '<i class="fas fa-moon"></i>';
}
function toggleTheme() { const n = chatApp.classList.contains('light') ? 'dark' : 'light'; localStorage.setItem('chatTheme', n); applyTheme(n); }

// --- History List ---
function renderList() {
    const el = document.getElementById('chatHistoryList');
    const chats = CH.all();
    if (!chats.length) { el.innerHTML = '<div style="padding:20px 8px;color:#4b5563;font-size:.85rem;text-align:center">Chưa có lịch sử</div>'; return; }

    // Group by date
    const now = new Date(), today = now.toDateString();
    const yesterday = new Date(now - 86400000).toDateString();
    const groups = {};
    chats.forEach(c => {
        const d = new Date(c.ts).toDateString();
        const label = d === today ? 'Hôm nay' : d === yesterday ? 'Hôm qua' : new Date(c.ts).toLocaleDateString('vi-VN');
        if (!groups[label]) groups[label] = [];
        groups[label].push(c);
    });

    let html = '';
    Object.entries(groups).forEach(([label, items]) => {
        html += `<div class="history-group-label">${label}</div>`;
        items.forEach(c => {
            html += `<div class="chat-history-item${c.id === curId ? ' active' : ''}" onclick="switchChat('${c.id}')">
                <span class="hi-icon"><i class="fas fa-message"></i></span>
                <span class="hi-title">${esc(c.title)}</span>
                <span class="hi-del" onclick="event.stopPropagation();delChat('${c.id}')"><i class="fas fa-xmark"></i></span>
            </div>`;
        });
    });
    el.innerHTML = html;
}

// --- Chat Ops ---
function newChat(silent) {
    const id = genId();
    CH.add(id, 'Cuộc trò chuyện mới');
    curId = id;
    fetch('/chatbot/clear', { method: 'POST' });
    clearUI();
    renderList();
    if (!silent) inputEl.focus();
}

function switchChat(id) {
    if (id === curId) return;
    curId = id;
    fetch('/chatbot/clear', { method: 'POST' });
    const c = CH.get(id);
    if (!c) return;
    clearUI();
    c.msgs.forEach(m => addMsgDOM(m.text, m.role, m.sources, m.dur, false));
    const sb = document.getElementById('suggestionsBar');
    if (sb) sb.style.display = c.msgs.length ? 'none' : 'flex';
    renderList();
    messagesEl.scrollTop = messagesEl.scrollHeight;
    inputEl.focus();
}

function loadChat(id) { switchChat(id); }

function delChat(id) {
    CH.rm(id);
    if (id === curId) { const a = CH.all(); a.length ? switchChat(a[0].id) : newChat(true); }
    renderList();
}

function clearChat() {
    fetch('/chatbot/clear', { method: 'POST' }).then(() => {
        const c = CH.get(curId);
        if (c) { c.msgs = []; CH.save(); }
        clearUI(); renderList();
    });
}

function clearAllHistory() {
    if (!confirm('Xóa tất cả lịch sử trò chuyện?')) return;
    CH.clear();
    fetch('/chatbot/clear', { method: 'POST' });
    newChat(true);
}

function clearUI() {
    messagesEl.querySelectorAll('.msg:not(.typing-indicator)').forEach(m => m.remove());
    const ws = document.getElementById('welcomeState');
    if (!ws) {
        const d = document.createElement('div'); d.className = 'welcome-state'; d.id = 'welcomeState';
        d.innerHTML = '<div class="welcome-icon"><i class="fas fa-robot"></i></div><h2 class="welcome-title">Xin chào Admin 👋</h2><p class="welcome-sub">Tôi có thể giúp gì hôm nay?</p>';
        messagesEl.insertBefore(d, typingEl);
    }
    const sb = document.getElementById('suggestionsBar');
    if (sb) sb.style.display = 'none';
}

// --- Messaging ---
function handleKey(e) { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); } }

async function sendMessage() {
    const text = inputEl.value.trim();
    if (!text || isLoading) return;
    addMsgDOM(text, 'user');
    CH.addMsg(curId, 'user', text);
    inputEl.value = ''; inputEl.style.height = 'auto';
    const sb = document.getElementById('suggestionsBar');
    if (sb) sb.style.display = 'none';
    setLoading(true);
    renderList();

    try {
        const response = await fetch('/chatbot/ask_stream', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question: text })
        });
        
        setLoading(false);

        const div = document.createElement('div');
        div.className = 'msg bot';
        div.innerHTML = `<div class="msg-avatar"><i class="fas fa-robot"></i></div><div class="msg-body"><div class="bubble"></div></div>`;
        messagesEl.insertBefore(div, typingEl);
        
        const bodyEl = div.querySelector('.msg-body');
        const bubble = bodyEl.querySelector('.bubble');
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');
        
        let fullAnswer = "";
        let sources = [];
        let durationMs = 0;

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value, { stream: true });
            const lines = chunk.split('\n');
            
            for (let line of lines) {
                if (line.startsWith('data: ')) {
                    const dataStr = line.replace('data: ', '').trim();
                    if (dataStr === '[DONE]') break;
                    try {
                        const parsed = JSON.parse(dataStr);
                        if (parsed.type === 'sources') {
                            sources = parsed.sources;
                        } else if (parsed.type === 'chunk') {
                            fullAnswer += parsed.text;
                            bubble.innerHTML = marked.parse(fullAnswer);
                            messagesEl.scrollTop = messagesEl.scrollHeight;
                        } else if (parsed.type === 'done') {
                            durationMs = parsed.duration_ms;
                        } else if (parsed.type === 'error') {
                            fullAnswer += "\n\n" + parsed.text;
                            bubble.innerHTML = marked.parse(fullAnswer);
                            messagesEl.scrollTop = messagesEl.scrollHeight;
                        }
                    } catch (e) {}
                }
            }
        }
        
        if (durationMs) {
            const metaDiv = document.createElement('div');
            metaDiv.className = 'meta';
            metaDiv.innerHTML = '⏱ ' + durationMs + 'ms';
            bodyEl.appendChild(metaDiv);
        }
        // if (sources && sources.length) {
        //     const s = [...new Set(sources.map(x => x.file))].join(', ');
        //     const sourcesDiv = document.createElement('div');
        //     sourcesDiv.className = 'sources';
        //     sourcesDiv.innerHTML = '📚 ' + s;
        //     bodyEl.appendChild(sourcesDiv);
        // }
        
        CH.addMsg(curId, 'bot', fullAnswer, sources, durationMs);
        
    } catch (err) {
        setLoading(false);
        const m = '❌ Lỗi: ' + err.message;
        addMsgDOM(m, 'bot');
        CH.addMsg(curId, 'bot', m);
    }
}

function addMsgDOM(text, role, sources, dur, animate = true) {
    const div = document.createElement('div');
    div.className = 'msg ' + role;
    if (!animate) div.style.animation = 'none';
    const icon = role === 'bot' ? 'fa-robot' : 'fa-user';
    let h = `<div class="msg-avatar"><i class="fas ${icon}"></i></div><div class="msg-body">`;
    h += '<div class="bubble">' + (role === 'bot' ? marked.parse(text) : esc(text)) + '</div>';
    if (role === 'bot' && dur) h += '<div class="meta">⏱ ' + dur + 'ms</div>';
    // if (sources && sources.length) { const s = [...new Set(sources.map(x => x.file))].join(', '); h += '<div class="sources">📚 ' + s + '</div>'; }
    h += '</div>';
    div.innerHTML = h;
    messagesEl.insertBefore(div, typingEl);
    messagesEl.scrollTop = messagesEl.scrollHeight;
}

function setLoading(v) {
    isLoading = v;
    typingEl.style.display = v ? 'flex' : 'none';
    document.getElementById('btnSend').disabled = v;
    if (v) messagesEl.scrollTop = messagesEl.scrollHeight;
}

function askSuggested(el) { inputEl.value = (el.querySelector('span') || el).textContent; sendMessage(); }

// --- Settings ---
function openSettings() { document.getElementById('settingsModal').classList.add('open'); }
function closeSettings() { document.getElementById('settingsModal').classList.remove('open'); }

// --- Knowledge Builder ---
function buildKnowledge() {
    const btn = document.getElementById('btnBuild');
    btn.disabled = true; btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Đang xây dựng...';
    fetch('/chatbot/build-knowledge', { method: 'POST' });
    document.getElementById('kbProgress').style.display = 'block';
    const es = new EventSource('/chatbot/knowledge-progress');
    es.onmessage = function (e) {
        const d = JSON.parse(e.data);
        document.getElementById('kbProgressBar').style.width = (d.progress * 100) + '%';
        if (d.status === 'done' || d.status === 'error') {
            es.close(); btn.disabled = false; btn.innerHTML = '<i class="fas fa-arrows-rotate"></i> Cập nhật KB';
            if (d.status === 'done') document.getElementById('kbProgress').style.display = 'none';
            setTimeout(() => location.reload(), 1500);
        }
    };
    es.onerror = () => { es.close(); btn.disabled = false; btn.innerHTML = '<i class="fas fa-arrows-rotate"></i> Cập nhật KB'; };
}

function esc(t) { const d = document.createElement('div'); d.textContent = t; return d.innerHTML; }

// ═══════════════════════════════════════════════════════════
// VOICE CHAT INTEGRATION
// ═══════════════════════════════════════════════════════════

(function initVoiceChat() {
    // Check support
    const support = VoiceEngine.isSupported();
    if (!support.full) {
        const btnMic = document.getElementById('btnMic');
        const btnVoiceMode = document.getElementById('btnVoiceMode');
        if (btnMic) btnMic.style.display = 'none';
        if (btnVoiceMode) btnVoiceMode.style.display = 'none';
        console.warn('[Voice] Browser does not support Speech API');
        return;
    }

    // DOM refs
    const overlay = document.getElementById('voiceOverlay');
    const voiceOrb = document.getElementById('voiceOrb');
    const voiceStatusText = document.getElementById('voiceStatusText');
    const voiceTranscript = document.getElementById('voiceTranscript');
    const btnMic = document.getElementById('btnMic');
    const btnVoiceMode = document.getElementById('btnVoiceMode');
    const voiceBtnMic = document.getElementById('voiceBtnMic');
    const voiceBtnStop = document.getElementById('voiceBtnStop');
    const voiceBtnClose = document.getElementById('voiceBtnClose');

    let voiceMode = false;
    let inlineMicActive = false;
    let voiceEngine = null;
    let isBusy = false;  // prevent double-send while processing

    // ─── Create Voice Engine ─────────────────────────────────

    function getEngine() {
        if (!voiceEngine) {
            voiceEngine = new VoiceEngine({
                lang: 'vi-VN',
                // preferredVoice: 'NamMinh', // <--- BỎ DẤU // ĐỂ ĐỔI GIỌNG (Ví dụ: 'NamMinh' hoặc 'HoaiMy')
                continuous: false,   // Use single-shot mode for reliability
                interimResults: true,
                autoRestart: false,  // We control restart manually

                onListeningStart() {
                    console.log('[Voice] 🎤 Listening started');
                    if (voiceMode) {
                        setOverlayState('listening');
                        voiceStatusText.textContent = 'Đang nghe...';
                        voiceBtnMic.classList.add('active');
                        voiceBtnMic.innerHTML = '<i class="fas fa-microphone-slash"></i>';
                    }
                    if (inlineMicActive) {
                        btnMic.classList.add('active');
                    }
                },

                onListeningEnd() {
                    console.log('[Voice] 🎤 Listening ended');
                    if (voiceMode) {
                        voiceBtnMic.classList.remove('active');
                        voiceBtnMic.innerHTML = '<i class="fas fa-microphone"></i>';
                    }
                    if (inlineMicActive) {
                        btnMic.classList.remove('active');
                        inlineMicActive = false;
                    }
                },

                onResult(text, isFinal) {
                    if (voiceMode) {
                        voiceTranscript.textContent = text;
                        voiceTranscript.classList.toggle('interim', !isFinal);
                    }
                    if (inlineMicActive && !isFinal) {
                        inputEl.value = text;
                        inputEl.style.height = 'auto';
                        inputEl.style.height = Math.min(inputEl.scrollHeight, 120) + 'px';
                    }
                },

                onFinalResult(text) {
                    if (!text) return;
                    console.log('[Voice] 📝 Final result:', text);

                    if (voiceMode && !isBusy) {
                        voiceTranscript.textContent = text;
                        voiceTranscript.classList.remove('interim');
                        voiceSendAndSpeak(text);
                    } else if (inlineMicActive) {
                        inputEl.value = text;
                        voiceEngine.stopListening();
                        inlineMicActive = false;
                        sendMessage();
                    }
                },

                onSpeakStart() {
                    console.log('[Voice] 🔊 Speaking started');
                    if (voiceMode) {
                        setOverlayState('speaking');
                        voiceStatusText.textContent = 'AI đang trả lời...';
                    }
                },

                onSpeakEnd() {
                    console.log('[Voice] 🔊 Speaking ended');
                    isBusy = false;

                    if (voiceMode) {
                        // Auto-restart listening for continuous conversation
                        voiceTranscript.textContent = '';
                        setOverlayState('idle');
                        voiceStatusText.textContent = 'Đang chuẩn bị nghe...';

                        setTimeout(() => {
                            if (voiceMode) {
                                console.log('[Voice] 🔄 Auto-restarting listening...');
                                restartListening();
                            }
                        }, 800);
                    }
                },

                onError(msg) {
                    console.error('[Voice] ❌', msg);
                    isBusy = false;
                    if (voiceMode) {
                        voiceStatusText.textContent = msg;
                        setTimeout(() => {
                            if (voiceMode) voiceStatusText.textContent = 'Bấm mic để thử lại';
                        }, 3000);
                    }
                },

                onVolumeChange(level) {
                    if (voiceMode && voiceOrb) {
                        const scale = 1 + level * 0.3;
                        voiceOrb.style.transform = `scale(${scale})`;
                    }
                }
            });
        }
        return voiceEngine;
    }

    // ─── Restart listening (force fresh start) ───────────────

    function restartListening() {
        const engine = getEngine();
        // Force clean state
        engine.stopListening();
        engine.stopSpeaking();
        engine._stopped = false;

        // Small delay to let recognition fully stop before restarting
        setTimeout(() => {
            if (voiceMode) {
                console.log('[Voice] 🎤 Starting fresh listen...');
                engine.startListening();
            }
        }, 200);
    }

    // ─── Overlay State Machine ───────────────────────────────

    function setOverlayState(state) {
        overlay.classList.remove('listening', 'speaking', 'processing');
        if (state) overlay.classList.add(state);
    }

    // ─── Voice Mode: Send text and speak response ────────────

    function voiceSendAndSpeak(text) {
        isBusy = true;

        // Stop listening during API call
        const engine = getEngine();
        engine.stopListening();
        setOverlayState('processing');
        voiceStatusText.textContent = 'Đang suy nghĩ...';

        // Also add to chat UI
        addMsgDOM(text, 'user');
        CH.addMsg(curId, 'user', text);
        renderList();

        fetch('/chatbot/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question: text })
        })
        .then(r => r.json())
        .then(data => {
            // Add response to chat UI
            addMsgDOM(data.answer, 'bot', data.sources, data.duration_ms);
            CH.addMsg(curId, 'bot', data.answer, data.sources, data.duration_ms);

            // Show answer in voice transcript
            const cleanPreview = data.answer.replace(/[#*`_\[\]()]/g, '').substring(0, 100);
            voiceTranscript.textContent = cleanPreview + (data.answer.length > 100 ? '...' : '');
            voiceTranscript.classList.remove('interim');

            // Speak the answer — onSpeakEnd will auto-restart listening
            if (voiceMode) {
                console.log('[Voice] 🔊 Speaking response...');
                engine.speak(data.answer);
            } else {
                isBusy = false;
            }
        })
        .catch(err => {
            isBusy = false;
            const errMsg = '❌ Lỗi: ' + err.message;
            addMsgDOM(errMsg, 'bot');
            CH.addMsg(curId, 'bot', errMsg);

            if (voiceMode) {
                voiceStatusText.textContent = 'Có lỗi xảy ra';
                setOverlayState('idle');
                // Auto-restart listening after error
                setTimeout(() => {
                    if (voiceMode) {
                        restartListening();
                    }
                }, 2000);
            }
        });
    }

    // ─── Open/Close Fullscreen Voice Mode ────────────────────

    function openVoiceMode() {
        voiceMode = true;
        isBusy = false;
        overlay.classList.add('open');
        voiceTranscript.textContent = '';
        voiceStatusText.textContent = 'Đang bắt đầu...';
        setOverlayState('idle');
        document.body.style.overflow = 'hidden';

        // Init engine
        getEngine();

        // Start listening
        setTimeout(() => {
            if (voiceMode) {
                restartListening();
            }
        }, 500);
    }

    function closeVoiceMode() {
        voiceMode = false;
        isBusy = false;
        overlay.classList.remove('open');
        setOverlayState('');
        document.body.style.overflow = '';

        if (voiceEngine) {
            voiceEngine.stopListening();
            voiceEngine.stopSpeaking();
        }
    }

    // ─── Inline Mic (quick voice input) ──────────────────────

    function toggleInlineMic() {
        const engine = getEngine();

        if (inlineMicActive) {
            engine.stopListening();
            inlineMicActive = false;
            btnMic.classList.remove('active');
        } else {
            inlineMicActive = true;
            inputEl.value = '';
            engine.startListening();
        }
    }

    // ─── Event Listeners ─────────────────────────────────────

    if (btnVoiceMode) {
        btnVoiceMode.addEventListener('click', () => openVoiceMode());
    }

    if (btnMic) {
        btnMic.addEventListener('click', (e) => {
            e.preventDefault();
            toggleInlineMic();
        });
    }

    if (voiceBtnMic) {
        voiceBtnMic.addEventListener('click', () => {
            const engine = getEngine();
            if (engine.isListening) {
                engine.stopListening();
                setOverlayState('idle');
                voiceStatusText.textContent = 'Bấm mic để nói';
            } else {
                voiceTranscript.textContent = '';
                restartListening();
            }
        });
    }

    if (voiceBtnStop) {
        voiceBtnStop.addEventListener('click', () => {
            const engine = getEngine();
            engine.stopSpeaking();
            isBusy = false;
            setOverlayState('idle');
            voiceStatusText.textContent = 'Đã dừng. Bấm mic để nói';
        });
    }

    if (voiceBtnClose) {
        voiceBtnClose.addEventListener('click', () => closeVoiceMode());
    }

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && voiceMode) closeVoiceMode();
    });

    if (window.speechSynthesis) {
        window.speechSynthesis.getVoices();
        window.speechSynthesis.onvoiceschanged = () => window.speechSynthesis.getVoices();
    }

    console.log('[Voice] Voice Chat initialized ✓');
})();