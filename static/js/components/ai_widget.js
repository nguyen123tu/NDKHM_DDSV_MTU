/* ai_widget.js — Logic for Floating Chat Widget */

document.addEventListener('DOMContentLoaded', () => {
    const fab = document.getElementById('aiWidgetFab');
    const container = document.getElementById('aiWidgetContainer');
    const closeBtn = document.getElementById('aiWidgetClose');
    const clearBtn = document.getElementById('aiWidgetClear');
    const input = document.getElementById('aiWidgetInput');
    const sendBtn = document.getElementById('aiWidgetSend');
    const messagesArea = document.getElementById('aiWidgetMessages');
    const typingIndicator = document.getElementById('aiWidgetTyping');
    const welcomeState = document.getElementById('aiWelcomeState');

    let isAiLoading = false;
    let chatHistory = JSON.parse(sessionStorage.getItem('aiWidgetHistory')) || [];
    const conversationId = 'widget';

    function safeMarkdown(text) {
        const html = marked.parse(String(text || ''));
        return DOMPurify.sanitize(html, { USE_PROFILES: { html: true } });
    }

    // Init history
    if (chatHistory.length > 0) {
        if (welcomeState) welcomeState.style.display = 'none';
        chatHistory.forEach(m => addMessageToDOM(m.text, m.role, false));
    }

    // Toggle Widget
    function toggleWidget() {
        const isOpen = container.classList.contains('open');
        if (isOpen) {
            container.classList.remove('open');
        } else {
            container.classList.add('open');
            input.focus();
            scrollToBottom();
        }
    }

    fab.addEventListener('click', toggleWidget);
    closeBtn.addEventListener('click', toggleWidget);

    clearBtn.addEventListener('click', () => {
        if (confirm('Bạn có chắc chắn muốn xóa lịch sử chat này?')) {
            sessionStorage.removeItem('aiWidgetHistory');
            chatHistory = [];
            messagesArea.querySelectorAll('.ai-msg:not(.ai-typing)').forEach(el => el.remove());
            if (welcomeState) welcomeState.style.display = 'flex';
            fetch('/chatbot/clear', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ conversation_id: conversationId })
            });
        }
    });

    // Handle Input Height Auto-resize
    input.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 100) + 'px';
    });

    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendAiMessage();
        }
    });

    sendBtn.addEventListener('click', sendAiMessage);

    // Global function for suggestion chips
    window.askAiWidget = function(text) {
        input.value = text;
        sendAiMessage();
    };

    function scrollToBottom() {
        messagesArea.scrollTop = messagesArea.scrollHeight;
    }

    async function sendAiMessage() {
        const text = input.value.trim();
        if (!text || isAiLoading) return;

        // User message
        addMessageToDOM(text, 'user');
        chatHistory.push({ role: 'user', text: text });
        sessionStorage.setItem('aiWidgetHistory', JSON.stringify(chatHistory));
        
        input.value = '';
        input.style.height = 'auto';
        if (welcomeState) welcomeState.style.display = 'none';

        isAiLoading = true;
        typingIndicator.style.display = 'flex';
        sendBtn.disabled = true;
        scrollToBottom();

        try {
            const response = await fetch('/chatbot/ask_stream', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    question: text,
                    conversation_id: conversationId
                })
            });

            if (!response.ok || !response.body) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.message || errorData.error || `HTTP ${response.status}`);
            }

            typingIndicator.style.display = 'none';
            isAiLoading = false;
            sendBtn.disabled = false;

            // Create bot message container
            const div = document.createElement('div');
            div.className = 'ai-msg bot';
            div.innerHTML = `<div class="ai-msg-avatar"><i class="material-symbols-outlined">auto_awesome</i></div><div class="ai-bubble"></div>`;
            messagesArea.insertBefore(div, typingIndicator);
            
            const bubble = div.querySelector('.ai-bubble');
            const reader = response.body.getReader();
            const decoder = new TextDecoder('utf-8');
            let fullAnswer = "";

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
                            if (parsed.type === 'chunk' || parsed.type === 'error') {
                                fullAnswer += parsed.text;
                                bubble.innerHTML = safeMarkdown(fullAnswer);
                                scrollToBottom();
                            }
                        } catch (e) {}
                    }
                }
            }

            chatHistory.push({ role: 'bot', text: fullAnswer });
            sessionStorage.setItem('aiWidgetHistory', JSON.stringify(chatHistory));

        } catch (error) {
            typingIndicator.style.display = 'none';
            isAiLoading = false;
            sendBtn.disabled = false;
            const errText = "Lỗi kết nối tới AI. Vui lòng thử lại.";
            addMessageToDOM(errText, 'bot');
            chatHistory.push({ role: 'bot', text: errText });
        }
    }

    function addMessageToDOM(text, role, animate = true) {
        const div = document.createElement('div');
        div.className = 'ai-msg ' + role;
        if (!animate) div.style.animation = 'none';
        
        const avatar = role === 'bot' 
            ? '<div class="ai-msg-avatar"><i class="material-symbols-outlined">auto_awesome</i></div>' 
            : '<div class="ai-msg-avatar"></div>';
            
        div.innerHTML = `${avatar}<div class="ai-bubble">${role === 'bot' ? safeMarkdown(text) : escapeHTML(text)}</div>`;
        messagesArea.insertBefore(div, typingIndicator);
        scrollToBottom();
    }

    function escapeHTML(str) {
        return str.replace(/[&<>'"]/g, 
            tag => ({
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                "'": '&#39;',
                '"': '&quot;'
            }[tag] || tag)
        );
    }
});
