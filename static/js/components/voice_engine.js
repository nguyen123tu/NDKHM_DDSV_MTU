/**
 * VoiceEngine — STT/TTS module for MTUFace AI Voice Chat
 * Uses Web Speech API (SpeechRecognition + SpeechSynthesis)
 * Supports Vietnamese (vi-VN)
 */

class VoiceEngine {
    constructor(options = {}) {
        this.lang = options.lang || 'vi-VN';
        this.continuous = options.continuous !== false;
        this.autoRestart = options.autoRestart !== false;
        this.interimResults = options.interimResults !== false;
        this.preferredVoice = options.preferredVoice || ''; // Custom voice name

        // State
        this.isListening = false;
        this.isSpeaking = false;
        this._recognition = null;
        this._synth = window.speechSynthesis;
        this._currentUtterance = null;
        this._restartTimeout = null;
        this._stopped = false; // explicit stop flag
        this._viVoice = null;  // cached Vietnamese voice
        this._voicesLoaded = false;
        this._speakQueue = [];  // queue for chunked speech
        this._chromaResumeInterval = null; // Chrome bug workaround

        // Callbacks
        this.onListeningStart = options.onListeningStart || (() => {});
        this.onListeningEnd = options.onListeningEnd || (() => {});
        this.onResult = options.onResult || (() => {});           // (text, isFinal)
        this.onFinalResult = options.onFinalResult || (() => {}); // (text)
        this.onSpeakStart = options.onSpeakStart || (() => {});
        this.onSpeakEnd = options.onSpeakEnd || (() => {});
        this.onError = options.onError || (() => {});
        this.onVolumeChange = options.onVolumeChange || (() => {}); // (level 0-1)

        // Audio analyzer for mic volume visualization
        this._audioCtx = null;
        this._analyser = null;
        this._micStream = null;

        this._initRecognition();
        this._preloadVoices();
    }

    // ─── Voice Preloading ───────────────────────────────────

    _preloadVoices() {
        if (!this._synth) return;

        const loadVoices = () => {
            const voices = this._synth.getVoices();
            if (voices.length === 0) return;

            this._voicesLoaded = true;

            // Log all available voices for debugging
            console.log('[VoiceEngine] Available voices (' + voices.length + '):');
            voices.forEach((v, i) => {
                const flag = v.lang.startsWith('vi') ? ' ⭐ VIETNAMESE' : '';
                console.log(`  [${i}] "${v.name}" (${v.lang}) ${v.localService ? 'local' : 'remote'}${flag}`);
            });

            const viVoices = voices.filter(v => 
                v.lang === 'vi-VN' || 
                v.lang === 'vi' || 
                v.lang.toLowerCase().startsWith('vi') || 
                /viet/i.test(v.name)
            );

            // Prioritize high-quality neural voices
            this._viVoice =
                (this.preferredVoice ? viVoices.find(v => v.name.includes(this.preferredVoice)) : null) ||
                viVoices.find(v => v.name.includes('Natural') || v.name.includes('Online')) ||
                viVoices.find(v => v.name.includes('Google')) ||
                viVoices[0] ||
                null;

            if (this._viVoice) {
                console.log(`[VoiceEngine] ✅ Vietnamese voice found: "${this._viVoice.name}" (${this._viVoice.lang})`);
            } else {
                console.warn('[VoiceEngine] ⚠️ Không tìm thấy giọng tiếng Việt! TTS sẽ dùng giọng mặc định.');
            }
        };

        // Try immediately
        loadVoices();

        // Also listen for async voice loading (Chrome loads voices async)
        this._synth.onvoiceschanged = () => {
            loadVoices();
        };

        // Retry a few times in case voices load slowly
        if (!this._voicesLoaded) {
            setTimeout(loadVoices, 500);
            setTimeout(loadVoices, 1500);
            setTimeout(loadVoices, 3000);
        }
    }

    // ─── STT Setup ──────────────────────────────────────────

    _initRecognition() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            console.warn('[VoiceEngine] SpeechRecognition not supported');
            return;
        }

        const rec = new SpeechRecognition();
        rec.lang = this.lang;
        rec.continuous = this.continuous;
        rec.interimResults = this.interimResults;
        rec.maxAlternatives = 1;

        rec.onstart = () => {
            this.isListening = true;
            this.onListeningStart();
        };

        rec.onend = () => {
            this.isListening = false;
            this.onListeningEnd();

            // Auto-restart if not explicitly stopped and not speaking
            if (this.autoRestart && !this._stopped && !this.isSpeaking) {
                this._restartTimeout = setTimeout(() => {
                    if (!this._stopped && !this.isSpeaking) {
                        this._safeStart();
                    }
                }, 300);
            }
        };

        rec.onresult = (event) => {
            let interimText = '';
            let finalText = '';

            for (let i = event.resultIndex; i < event.results.length; i++) {
                const transcript = event.results[i][0].transcript;
                if (event.results[i].isFinal) {
                    finalText += transcript;
                } else {
                    interimText += transcript;
                }
            }

            if (interimText) {
                this.onResult(interimText, false);
            }
            if (finalText) {
                this.onResult(finalText, true);
                this.onFinalResult(finalText.trim());
            }
        };

        rec.onerror = (event) => {
            console.warn('[VoiceEngine] STT error:', event.error);

            if (event.error === 'no-speech' || event.error === 'aborted') {
                // These are non-fatal — auto restart will handle
                return;
            }

            if (event.error === 'not-allowed') {
                this.onError('Microphone bị chặn. Vui lòng cấp quyền truy cập mic.');
                this._stopped = true;
            } else {
                this.onError(`Lỗi nhận diện giọng nói: ${event.error}`);
            }
        };

        rec.onsoundstart = () => {
            this._startAudioAnalysis();
        };

        this._recognition = rec;
    }

    // ─── Mic Volume Analysis ────────────────────────────────

    async _startAudioAnalysis() {
        if (this._analyser) return;

        try {
            if (!this._audioCtx) {
                this._audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            }

            if (!this._micStream) {
                this._micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
            }

            const source = this._audioCtx.createMediaStreamSource(this._micStream);
            this._analyser = this._audioCtx.createAnalyser();
            this._analyser.fftSize = 256;
            this._analyser.smoothingTimeConstant = 0.7;
            source.connect(this._analyser);

            this._pollVolume();
        } catch (e) {
            console.warn('[VoiceEngine] Audio analysis failed:', e);
        }
    }

    _pollVolume() {
        if (!this._analyser || !this.isListening) {
            this.onVolumeChange(0);
            return;
        }

        const data = new Uint8Array(this._analyser.frequencyBinCount);
        this._analyser.getByteFrequencyData(data);

        // Calculate RMS volume level (0-1)
        let sum = 0;
        for (let i = 0; i < data.length; i++) {
            sum += data[i] * data[i];
        }
        const rms = Math.sqrt(sum / data.length) / 255;
        const level = Math.min(1, rms * 2.5); // amplify a bit

        this.onVolumeChange(level);
        requestAnimationFrame(() => this._pollVolume());
    }

    _stopAudioAnalysis() {
        this._analyser = null;
        if (this._micStream) {
            this._micStream.getTracks().forEach(t => t.stop());
            this._micStream = null;
        }
        this.onVolumeChange(0);
    }

    // ─── STT Controls ───────────────────────────────────────

    startListening() {
        if (!this._recognition) {
            this.onError('Trình duyệt không hỗ trợ nhận diện giọng nói. Hãy dùng Chrome hoặc Edge.');
            return false;
        }

        // Stop TTS if it's speaking
        this.stopSpeaking();

        this._stopped = false;
        clearTimeout(this._restartTimeout);
        this._safeStart();
        return true;
    }

    stopListening() {
        this._stopped = true;
        clearTimeout(this._restartTimeout);

        if (this._recognition && this.isListening) {
            this._recognition.stop();
        }

        this._stopAudioAnalysis();
        this.isListening = false;
    }

    _safeStart() {
        try {
            if (!this.isListening) {
                this._recognition.start();
            }
        } catch (e) {
            // Already started — ignore
            console.warn('[VoiceEngine] Start warning:', e.message);
        }
    }

    // ─── TTS Controls ───────────────────────────────────────

    speak(text) {
        // Stop listening while speaking
        this.stopListening();

        // Cancel any ongoing speech
        this.stopSpeaking();

        if (!text || !text.trim()) {
            this.onSpeakEnd();
            return;
        }

        // Check if we have a high-quality browser voice (Edge Natural or Google)
        const isHighQualityVoice = this._viVoice && (
            this._viVoice.name.includes('Natural') || 
            this._viVoice.name.includes('Google') ||
            this._viVoice.name.includes('Online')
        );

        if (isHighQualityVoice) {
            console.log('[VoiceEngine] ✨ Using high-quality browser voice:', this._viVoice.name);
            this._speakFallback(text);
        } else {
            console.log('[VoiceEngine] 🤖 Using backend gTTS fallback');
            this._speakViaBackend(text);
        }
    }

    /**
     * Fallback to Backend TTS: Send text to backend /chatbot/tts endpoint
     * Uses gTTS (Google Text-to-Speech)
     */
    _speakViaBackend(text) {
        console.log('[VoiceEngine] Requesting backend gTTS');

        this.isSpeaking = true;
        this.onSpeakStart();

        fetch('/chatbot/tts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: text,
                voice: 'vi-VN-HoaiMyNeural'  // Female Vietnamese neural voice
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`TTS API error: ${response.status}`);
            }
            return response.blob();
        })
        .then(blob => {
            const audioUrl = URL.createObjectURL(blob);
            this._audioEl = new Audio(audioUrl);
            this._audioEl.volume = 1.0;

            this._audioEl.onended = () => {
                URL.revokeObjectURL(audioUrl);
                this._audioEl = null;
                this.isSpeaking = false;
                this.onSpeakEnd();
            };

            this._audioEl.onerror = (e) => {
                console.warn('[VoiceEngine] Audio playback error:', e);
                URL.revokeObjectURL(audioUrl);
                this._audioEl = null;
                this.isSpeaking = false;
                this.onSpeakEnd();
            };

            this._audioEl.play().catch(err => {
                console.warn('[VoiceEngine] Audio play blocked:', err);
                // Fallback to Web Speech API
                this._audioEl = null;
                this._speakFallback(text);
            });
        })
        .catch(err => {
            console.warn('[VoiceEngine] Backend TTS failed, using fallback:', err.message);
            // Fallback to Web Speech API
            this._speakFallback(text);
        });
    }

    /**
     * Fallback TTS: Web Speech API (may not have Vietnamese voice)
     * Used when backend TTS is unavailable
     */
    _speakFallback(text) {
        if (!this._synth) {
            this.isSpeaking = false;
            this.onSpeakEnd();
            return;
        }

        console.log('[VoiceEngine] Fallback: using Web Speech API TTS');
        this._synth.cancel();

        const cleanText = this._cleanForSpeech(text);
        if (!cleanText) {
            this.isSpeaking = false;
            this.onSpeakEnd();
            return;
        }

        // Split into chunks to avoid Chrome TTS cutoff bug
        this._speakQueue = this._splitIntoChunks(cleanText, 180);
        this._speakNextChunk();
    }

    _speakNextChunk() {
        if (this._speakQueue.length === 0) {
            this.isSpeaking = false;
            this._currentUtterance = null;
            this.onSpeakEnd();
            return;
        }

        const chunkText = this._speakQueue.shift();
        const utterance = new SpeechSynthesisUtterance(chunkText);
        utterance.lang = this.lang;
        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        utterance.volume = 1.0;

        if (this._viVoice) {
            utterance.voice = this._viVoice;
        }

        utterance.onend = () => {
            setTimeout(() => this._speakNextChunk(), 80);
        };

        utterance.onerror = (e) => {
            if (e.error !== 'interrupted' && e.error !== 'canceled') {
                console.warn('[VoiceEngine] TTS chunk error:', e.error);
            }
            if (this._speakQueue.length > 0 && e.error !== 'interrupted' && e.error !== 'canceled') {
                setTimeout(() => this._speakNextChunk(), 100);
            } else {
                this.isSpeaking = false;
                this._currentUtterance = null;
                this.onSpeakEnd();
            }
        };

        this._currentUtterance = utterance;
        this._synth.speak(utterance);
    }

    _splitIntoChunks(text, maxLen = 180) {
        if (text.length <= maxLen) return [text];

        const chunks = [];
        const sentences = text.split(/(?<=[.!?;:]\s)/);
        let current = '';

        for (const sentence of sentences) {
            if ((current + sentence).length > maxLen && current.length > 0) {
                chunks.push(current.trim());
                current = sentence;
            } else {
                current += sentence;
            }
        }

        if (current.trim()) {
            if (current.length > maxLen) {
                const subParts = current.split(/(?<=[,，]\s)/);
                let sub = '';
                for (const part of subParts) {
                    if ((sub + part).length > maxLen && sub.length > 0) {
                        chunks.push(sub.trim());
                        sub = part;
                    } else {
                        sub += part;
                    }
                }
                if (sub.trim()) chunks.push(sub.trim());
            } else {
                chunks.push(current.trim());
            }
        }

        return chunks.filter(c => c.length > 0);
    }

    stopSpeaking() {
        // Stop backend audio
        if (this._audioEl) {
            this._audioEl.pause();
            this._audioEl.currentTime = 0;
            this._audioEl = null;
        }

        // Stop fallback Web Speech API
        this._speakQueue = [];
        if (this._synth) {
            this._synth.cancel();
        }
        this.isSpeaking = false;
        this._currentUtterance = null;
    }

    // ─── Helpers ─────────────────────────────────────────────

    _cleanForSpeech(text) {
        return text
            .replace(/\*\*(.*?)\*\*/g, '$1')
            .replace(/\*(.*?)\*/g, '$1')
            .replace(/#{1,6}\s*/g, '')
            .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
            .replace(/```[\s\S]*?```/g, '')
            .replace(/`([^`]+)`/g, '$1')
            .replace(/^[\s]*[-•*]\s*/gm, '')
            .replace(/[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{1F1E0}-\u{1F1FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/gu, '')
            .replace(/\n{2,}/g, '. ')
            .replace(/\n/g, '. ')
            .replace(/\s{2,}/g, ' ')
            .trim();
    }

    /**
     * Check if voice features are supported
     * STT requires Web Speech API, TTS works via backend (always available)
     */
    static isSupported() {
        const hasSTT = !!(window.SpeechRecognition || window.webkitSpeechRecognition);
        // TTS is always available via backend edge-tts
        return { stt: hasSTT, tts: true, full: hasSTT };
    }

    /**
     * Destroy and clean up
     */
    destroy() {
        this.stopListening();
        this.stopSpeaking();
        if (this._audioCtx) {
            this._audioCtx.close().catch(() => {});
            this._audioCtx = null;
        }
    }
}

// Export for global use
window.VoiceEngine = VoiceEngine;

