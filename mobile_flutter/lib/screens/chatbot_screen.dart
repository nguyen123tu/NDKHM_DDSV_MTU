import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import '../services/api_service.dart';
import '../theme/app_theme.dart';

/// Model đại diện một tin nhắn chat
class ChatMessage {
  final String text;
  final bool isUser;
  final DateTime timestamp;
  final List<Map<String, dynamic>>? sources;
  final int? durationMs;

  ChatMessage({
    required this.text,
    required this.isUser,
    DateTime? timestamp,
    this.sources,
    this.durationMs,
  }) : timestamp = timestamp ?? DateTime.now();
}

class ChatbotScreen extends StatefulWidget {
  const ChatbotScreen({super.key});

  @override
  State<ChatbotScreen> createState() => _ChatbotScreenState();
}

class _ChatbotScreenState extends State<ChatbotScreen>
    with TickerProviderStateMixin {
  final ApiService _api = ApiService();
  final TextEditingController _controller = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final FocusNode _focusNode = FocusNode();

  final List<ChatMessage> _messages = [];
  List<String> _suggestions = [];
  bool _isLoading = false;
  bool _hasError = false;

  @override
  void initState() {
    super.initState();
    _loadSuggestions();
  }

  @override
  void dispose() {
    _controller.dispose();
    _scrollController.dispose();
    _focusNode.dispose();
    super.dispose();
  }

  Future<void> _loadSuggestions() async {
    final suggestions = await _api.getChatbotSuggestions();
    if (mounted) {
      setState(() => _suggestions = suggestions);
    }
  }

  Future<void> _sendMessage(String text) async {
    if (text.trim().isEmpty) return;

    final question = text.trim();
    _controller.clear();

    setState(() {
      _messages.add(ChatMessage(text: question, isUser: true));
      _isLoading = true;
      _hasError = false;
    });

    _scrollToBottom();

    final result = await _api.askChatbot(question);

    if (!mounted) return;

    setState(() {
      _isLoading = false;
      if (result['success'] == true) {
        final data = result['data'] ?? {};
        _messages.add(ChatMessage(
          text: data['answer'] ?? 'Không nhận được câu trả lời.',
          isUser: false,
          sources: data['sources'] != null
              ? List<Map<String, dynamic>>.from(data['sources'])
              : null,
          durationMs: data['duration_ms'],
        ));
      } else {
        _hasError = true;
        _messages.add(ChatMessage(
          text: result['message'] ?? 'Đã xảy ra lỗi khi gọi AI.',
          isUser: false,
        ));
      }
    });

    _scrollToBottom();
  }

  void _scrollToBottom() {
    Future.delayed(const Duration(milliseconds: 150), () {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent + 100,
          duration: const Duration(milliseconds: 400),
          curve: Curves.easeOutCubic,
        );
      }
    });
  }

  Future<void> _clearHistory() async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppTheme.surface,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: const Text('Xóa lịch sử chat?',
            style: TextStyle(color: AppTheme.textPrimary)),
        content: const Text(
          'Toàn bộ cuộc trò chuyện sẽ bị xóa và không thể khôi phục.',
          style: TextStyle(color: AppTheme.textSecondary),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Hủy',
                style: TextStyle(color: AppTheme.textMuted)),
          ),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            child:
                const Text('Xóa', style: TextStyle(color: AppTheme.accent)),
          ),
        ],
      ),
    );

    if (confirm == true) {
      await _api.clearChatHistory();
      if (mounted) {
        setState(() => _messages.clear());
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: const Text('Đã xóa lịch sử chat'),
            backgroundColor: AppTheme.surface,
            behavior: SnackBarBehavior.floating,
            shape:
                RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.background,
      body: Stack(
        children: [
          // Ambient glows
          Positioned(
            top: -80,
            right: -80,
            child: Container(
              width: 250,
              height: 250,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: AppTheme.secondary.withOpacity(0.12),
              ),
            )
                .animate(
                    onPlay: (controller) => controller.repeat(reverse: true))
                .scale(
                    begin: const Offset(1, 1),
                    end: const Offset(1.3, 1.3),
                    duration: 5.seconds),
          ),
          Positioned(
            bottom: -60,
            left: -60,
            child: Container(
              width: 200,
              height: 200,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: AppTheme.primary.withOpacity(0.1),
              ),
            )
                .animate(
                    onPlay: (controller) => controller.repeat(reverse: true))
                .scale(
                    begin: const Offset(1, 1),
                    end: const Offset(1.2, 1.2),
                    duration: 4.seconds),
          ),

          // Main content
          SafeArea(
            child: Column(
              children: [
                _buildHeader(),
                Expanded(
                  child: _messages.isEmpty
                      ? _buildEmptyState()
                      : _buildMessageList(),
                ),
                if (_isLoading) _buildTypingIndicator(),
                _buildInputBar(),
              ],
            ),
          ),
        ],
      ),
    );
  }

  // ====== HEADER ======
  Widget _buildHeader() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      child: Row(
        children: [
          GestureDetector(
            onTap: () => Navigator.pop(context),
            child: Container(
              padding: const EdgeInsets.all(8),
              decoration: AppTheme.glassDecoration(
                  shape: BoxShape.circle, opacity: 0.08),
              child: const Icon(Icons.arrow_back_ios_new,
                  color: AppTheme.textPrimary, size: 18),
            ),
          ),
          const SizedBox(width: 12),
          // AI Avatar
          Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              gradient: const LinearGradient(
                colors: [AppTheme.secondary, AppTheme.primary],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              boxShadow: [
                BoxShadow(
                    color: AppTheme.secondary.withOpacity(0.3),
                    blurRadius: 12,
                    spreadRadius: 0),
              ],
            ),
            child: const Icon(Icons.auto_awesome, color: Colors.white, size: 20),
          )
              .animate(
                  onPlay: (controller) => controller.repeat(reverse: true))
              .scale(
                  begin: const Offset(1, 1),
                  end: const Offset(1.08, 1.08),
                  duration: 2.seconds),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'MTU AI Assistant',
                  style: TextStyle(
                    color: AppTheme.textPrimary,
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                Row(
                  children: [
                    Container(
                      width: 6,
                      height: 6,
                      decoration: const BoxDecoration(
                        shape: BoxShape.circle,
                        color: AppTheme.success,
                      ),
                    ),
                    const SizedBox(width: 4),
                    const Text(
                      'Online • RAG + AI',
                      style: TextStyle(
                          color: AppTheme.textMuted, fontSize: 11),
                    ),
                  ],
                ),
              ],
            ),
          ),
          GestureDetector(
            onTap: _messages.isNotEmpty ? _clearHistory : null,
            child: Container(
              padding: const EdgeInsets.all(8),
              decoration: AppTheme.glassDecoration(
                  shape: BoxShape.circle, opacity: 0.08),
              child: Icon(Icons.delete_outline,
                  color: _messages.isNotEmpty
                      ? AppTheme.accent
                      : AppTheme.textMuted,
                  size: 18),
            ),
          ),
        ],
      ),
    ).animate().fadeIn(duration: 400.ms).slideY(begin: -0.2, end: 0);
  }

  // ====== EMPTY STATE ======
  Widget _buildEmptyState() {
    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 24),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const SizedBox(height: 40),
          // Big AI icon
          Container(
            width: 100,
            height: 100,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              gradient: LinearGradient(
                colors: [
                  AppTheme.secondary.withOpacity(0.2),
                  AppTheme.primary.withOpacity(0.2),
                ],
              ),
              border:
                  Border.all(color: AppTheme.secondary.withOpacity(0.3), width: 2),
            ),
            child: const Icon(Icons.smart_toy_outlined,
                color: AppTheme.secondary, size: 48),
          )
              .animate()
              .fadeIn(delay: 200.ms, duration: 600.ms)
              .scale(begin: const Offset(0.5, 0.5), end: const Offset(1, 1)),

          const SizedBox(height: 24),
          const Text(
            'Xin chào! 👋',
            style: TextStyle(
              color: AppTheme.textPrimary,
              fontSize: 24,
              fontWeight: FontWeight.bold,
            ),
          ).animate().fadeIn(delay: 400.ms),

          const SizedBox(height: 8),
          Text(
            'Tôi là trợ lý AI của hệ thống MTUFace.\nHãy hỏi bất cứ điều gì về hệ thống điểm danh!',
            textAlign: TextAlign.center,
            style: TextStyle(
              color: AppTheme.textSecondary,
              fontSize: 14,
              height: 1.5,
            ),
          ).animate().fadeIn(delay: 500.ms),

          const SizedBox(height: 32),

          // Suggestions
          if (_suggestions.isNotEmpty) ...[
            Row(
              children: [
                Icon(Icons.lightbulb_outline,
                    color: AppTheme.warning.withOpacity(0.8), size: 16),
                const SizedBox(width: 6),
                const Text(
                  'Câu hỏi gợi ý',
                  style: TextStyle(
                    color: AppTheme.textSecondary,
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ).animate().fadeIn(delay: 600.ms),
            const SizedBox(height: 12),
            ...List.generate(
              _suggestions.length,
              (i) => _buildSuggestionCard(_suggestions[i], i),
            ),
          ],
          const SizedBox(height: 24),
        ],
      ),
    );
  }

  Widget _buildSuggestionCard(String text, int index) {
    return GestureDetector(
      onTap: () => _sendMessage(text),
      child: Container(
        width: double.infinity,
        margin: const EdgeInsets.only(bottom: 8),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        decoration: AppTheme.glassDecoration(
          borderRadius: 16,
          opacity: 0.06,
        ),
        child: Row(
          children: [
            const Icon(Icons.chat_bubble_outline,
                color: AppTheme.secondary, size: 16),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                text,
                style: const TextStyle(
                  color: AppTheme.textPrimary,
                  fontSize: 13,
                ),
              ),
            ),
            const Icon(Icons.arrow_forward_ios,
                color: AppTheme.textMuted, size: 12),
          ],
        ),
      ),
    )
        .animate()
        .fadeIn(delay: Duration(milliseconds: 650 + (index * 80)))
        .slideX(begin: 0.15, end: 0);
  }

  // ====== MESSAGE LIST ======
  Widget _buildMessageList() {
    return ListView.builder(
      controller: _scrollController,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      itemCount: _messages.length,
      itemBuilder: (context, index) {
        final msg = _messages[index];
        return _buildMessageBubble(msg, index);
      },
    );
  }

  Widget _buildMessageBubble(ChatMessage msg, int index) {
    final isUser = msg.isUser;

    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        constraints:
            BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.82),
        margin: const EdgeInsets.only(bottom: 12),
        child: Column(
          crossAxisAlignment:
              isUser ? CrossAxisAlignment.end : CrossAxisAlignment.start,
          children: [
            // Bubble
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              decoration: isUser
                  ? BoxDecoration(
                      gradient: const LinearGradient(
                        colors: [Color(0xFF4F46E5), Color(0xFF06B6D4)],
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      ),
                      borderRadius: BorderRadius.only(
                        topLeft: const Radius.circular(20),
                        topRight: const Radius.circular(20),
                        bottomLeft: const Radius.circular(20),
                        bottomRight: const Radius.circular(4),
                      ),
                      boxShadow: [
                        BoxShadow(
                          color: AppTheme.primary.withOpacity(0.25),
                          blurRadius: 12,
                          offset: const Offset(0, 4),
                        ),
                      ],
                    )
                  : BoxDecoration(
                      color: Colors.white.withOpacity(0.06),
                      borderRadius: BorderRadius.only(
                        topLeft: const Radius.circular(4),
                        topRight: const Radius.circular(20),
                        bottomLeft: const Radius.circular(20),
                        bottomRight: const Radius.circular(20),
                      ),
                      border: Border.all(
                          color: Colors.white.withOpacity(0.08), width: 1),
                    ),
              child: isUser
                  ? Text(
                      msg.text,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 14,
                        height: 1.5,
                      ),
                    )
                  : MarkdownBody(
                      data: msg.text,
                      selectable: true,
                      styleSheet: MarkdownStyleSheet(
                        p: const TextStyle(
                            color: AppTheme.textPrimary,
                            fontSize: 14,
                            height: 1.6),
                        h1: const TextStyle(
                            color: AppTheme.textPrimary,
                            fontSize: 20,
                            fontWeight: FontWeight.bold),
                        h2: const TextStyle(
                            color: AppTheme.textPrimary,
                            fontSize: 18,
                            fontWeight: FontWeight.bold),
                        h3: const TextStyle(
                            color: AppTheme.textPrimary,
                            fontSize: 16,
                            fontWeight: FontWeight.bold),
                        code: TextStyle(
                          color: AppTheme.secondary,
                          backgroundColor: AppTheme.primary.withOpacity(0.15),
                          fontSize: 13,
                          fontFamily: 'monospace',
                        ),
                        codeblockDecoration: BoxDecoration(
                          color: const Color(0xFF0D1117),
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(
                              color: Colors.white.withOpacity(0.1)),
                        ),
                        codeblockPadding: const EdgeInsets.all(12),
                        listBullet: const TextStyle(
                            color: AppTheme.secondary, fontSize: 14),
                        strong: const TextStyle(
                            color: AppTheme.secondary,
                            fontWeight: FontWeight.bold),
                        em: TextStyle(
                            color: AppTheme.textPrimary.withOpacity(0.9),
                            fontStyle: FontStyle.italic),
                        blockquoteDecoration: BoxDecoration(
                          color: AppTheme.primary.withOpacity(0.1),
                          borderRadius: BorderRadius.circular(4),
                          border: Border(
                            left: BorderSide(
                                color: AppTheme.secondary, width: 3),
                          ),
                        ),
                        tableBorder: TableBorder.all(
                            color: Colors.white.withOpacity(0.1)),
                        tableHead: const TextStyle(
                            color: AppTheme.textPrimary,
                            fontWeight: FontWeight.bold,
                            fontSize: 13),
                        tableBody: const TextStyle(
                            color: AppTheme.textSecondary, fontSize: 13),
                      ),
                    ),
            ),

            // Source badges + time
            if (!isUser) ...[
              const SizedBox(height: 6),
              Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  if (msg.durationMs != null)
                    Padding(
                      padding: const EdgeInsets.only(right: 8),
                      child: Text(
                        '${(msg.durationMs! / 1000).toStringAsFixed(1)}s',
                        style: TextStyle(
                          color: AppTheme.textMuted.withOpacity(0.6),
                          fontSize: 10,
                        ),
                      ),
                    ),
                  if (msg.sources != null && msg.sources!.isNotEmpty)
                    ...msg.sources!.take(2).map(
                          (s) => Container(
                            margin: const EdgeInsets.only(right: 4),
                            padding: const EdgeInsets.symmetric(
                                horizontal: 6, vertical: 2),
                            decoration: BoxDecoration(
                              color: AppTheme.secondary.withOpacity(0.1),
                              borderRadius: BorderRadius.circular(6),
                            ),
                            child: Text(
                              _shortenSource(s['file'] ?? ''),
                              style: const TextStyle(
                                color: AppTheme.secondary,
                                fontSize: 9,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ),
                        ),
                ],
              ),
            ],

            // Timestamp
            Padding(
              padding: const EdgeInsets.only(top: 4),
              child: Text(
                '${msg.timestamp.hour.toString().padLeft(2, '0')}:${msg.timestamp.minute.toString().padLeft(2, '0')}',
                style: TextStyle(
                  color: AppTheme.textMuted.withOpacity(0.5),
                  fontSize: 10,
                ),
              ),
            ),
          ],
        ),
      ),
    )
        .animate()
        .fadeIn(duration: 300.ms)
        .slideX(begin: isUser ? 0.15 : -0.15, end: 0);
  }

  String _shortenSource(String path) {
    final parts = path.split('/');
    return parts.length > 1 ? parts.last : path;
  }

  // ====== TYPING INDICATOR ======
  Widget _buildTypingIndicator() {
    return Align(
      alignment: Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
        decoration: BoxDecoration(
          color: Colors.white.withOpacity(0.06),
          borderRadius: const BorderRadius.only(
            topLeft: Radius.circular(4),
            topRight: Radius.circular(20),
            bottomLeft: Radius.circular(20),
            bottomRight: Radius.circular(20),
          ),
          border: Border.all(color: Colors.white.withOpacity(0.08)),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            _buildDot(0),
            const SizedBox(width: 4),
            _buildDot(1),
            const SizedBox(width: 4),
            _buildDot(2),
            const SizedBox(width: 10),
            Text(
              'Đang suy nghĩ...',
              style: TextStyle(
                color: AppTheme.textMuted.withOpacity(0.7),
                fontSize: 12,
                fontStyle: FontStyle.italic,
              ),
            ),
          ],
        ),
      ),
    ).animate().fadeIn(duration: 300.ms);
  }

  Widget _buildDot(int index) {
    return Container(
      width: 8,
      height: 8,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        color: AppTheme.secondary.withOpacity(0.7),
      ),
    )
        .animate(onPlay: (c) => c.repeat(reverse: true))
        .scale(
          begin: const Offset(0.5, 0.5),
          end: const Offset(1, 1),
          duration: 600.ms,
          delay: Duration(milliseconds: index * 150),
        )
        .then()
        .fadeOut(duration: 200.ms);
  }

  // ====== INPUT BAR ======
  Widget _buildInputBar() {
    return Container(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
      decoration: BoxDecoration(
        color: AppTheme.background.withOpacity(0.95),
        border: Border(
          top: BorderSide(color: Colors.white.withOpacity(0.05)),
        ),
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(24),
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
          child: Container(
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.07),
              borderRadius: BorderRadius.circular(24),
              border: Border.all(color: Colors.white.withOpacity(0.1)),
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Expanded(
                  child: TextField(
                    controller: _controller,
                    focusNode: _focusNode,
                    maxLines: 4,
                    minLines: 1,
                    style: const TextStyle(
                      color: AppTheme.textPrimary,
                      fontSize: 14,
                    ),
                    decoration: InputDecoration(
                      hintText: 'Hỏi về hệ thống MTUFace...',
                      hintStyle: TextStyle(
                        color: AppTheme.textMuted.withOpacity(0.5),
                        fontSize: 14,
                      ),
                      contentPadding: const EdgeInsets.symmetric(
                          horizontal: 20, vertical: 12),
                      border: InputBorder.none,
                    ),
                    onSubmitted: (text) {
                      if (!_isLoading) _sendMessage(text);
                    },
                  ),
                ),
                // Send button
                GestureDetector(
                  onTap: () {
                    if (!_isLoading && _controller.text.trim().isNotEmpty) {
                      _sendMessage(_controller.text);
                    }
                  },
                  child: Container(
                    margin: const EdgeInsets.only(right: 6, bottom: 6),
                    width: 40,
                    height: 40,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      gradient: LinearGradient(
                        colors: _isLoading
                            ? [AppTheme.textMuted, AppTheme.textMuted]
                            : [AppTheme.secondary, AppTheme.primary],
                      ),
                      boxShadow: _isLoading
                          ? []
                          : [
                              BoxShadow(
                                color: AppTheme.secondary.withOpacity(0.3),
                                blurRadius: 8,
                                offset: const Offset(0, 2),
                              ),
                            ],
                    ),
                    child: Icon(
                      _isLoading ? Icons.hourglass_top : Icons.arrow_upward,
                      color: Colors.white,
                      size: 18,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    ).animate().fadeIn(delay: 300.ms).slideY(begin: 0.3, end: 0);
  }
}
