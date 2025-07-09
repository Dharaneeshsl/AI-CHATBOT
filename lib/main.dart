import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:animated_text_kit/animated_text_kit.dart';

void main() {
  runApp(const DetroitApp());
}

class DetroitApp extends StatelessWidget {
  const DetroitApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'DETROIT',
      theme: ThemeData(
        brightness: Brightness.light,
        scaffoldBackgroundColor: Colors.grey[100],
        primarySwatch: Colors.blue,
        fontFamily: 'Roboto',
      ),
      home: const ChatScreen(),
      debugShowCheckedModeBanner: false,
    );
  }
}

class Message {
  final String text;
  final bool isUser;
  Message({required this.text, required this.isUser});
}

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final List<Message> _messages = [];
  final TextEditingController _controller = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  bool _isBotTyping = false;

  // Toggle this for testing without backend
  final bool _simulate = false;

  Future<void> _sendMessage(String text) async {
    if (text.trim().isEmpty) return;
    setState(() {
      _messages.add(Message(text: text, isUser: true));
      _isBotTyping = true;
    });
    _controller.clear();
    _scrollToBottom();

    String botReply;
    if (_simulate) {
      await Future.delayed(const Duration(seconds: 2));
      botReply = 'This is a dummy reply.';
    } else {
      try {
        final response = await http.post(
          Uri.parse('https://your-backend.com/query'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({'query': text}),
        );
        if (response.statusCode == 200) {
          final data = jsonDecode(response.body);
          botReply = data['response']?.toString() ?? 'No response.';
        } else {
          botReply = 'Sorry, something went wrong.';
        }
      } catch (_) {
        botReply = 'Sorry, something went wrong.';
      }
    }
    setState(() {
      _isBotTyping = false;
      _messages.add(Message(text: botReply, isUser: false));
    });
    _scrollToBottom();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent + 60,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  Widget _buildMessageBubble(Message message) {
    final isUser = message.isUser;
    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        constraints:
            BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.75),
        margin: const EdgeInsets.symmetric(vertical: 6, horizontal: 8),
        padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 16),
        decoration: BoxDecoration(
          color: isUser ? Colors.blueAccent : Colors.grey[300],
          borderRadius: BorderRadius.only(
            topLeft: const Radius.circular(18),
            topRight: const Radius.circular(18),
            bottomLeft: Radius.circular(isUser ? 18 : 4),
            bottomRight: Radius.circular(isUser ? 4 : 18),
          ),
        ),
        child: Text(
          message.text,
          style: TextStyle(
            color: isUser ? Colors.white : Colors.black,
            fontSize: 16,
          ),
        ),
      ),
    );
  }

  Widget _buildTypingIndicator() {
    return Align(
      alignment: Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 6, horizontal: 8),
        padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 16),
        decoration: BoxDecoration(
          color: Colors.grey[300],
          borderRadius: const BorderRadius.only(
            topLeft: Radius.circular(18),
            topRight: Radius.circular(18),
            bottomLeft: Radius.circular(18),
            bottomRight: Radius.circular(4),
          ),
        ),
        child: AnimatedTextKit(
          animatedTexts: [
            TyperAnimatedText('typing...',
                textStyle: const TextStyle(fontSize: 16)),
          ],
          isRepeatingAnimation: true,
          repeatForever: true,
          pause: const Duration(milliseconds: 500),
          displayFullTextOnTap: false,
        ),
      ),
    );
  }

  Widget _buildInputBar() {
    return Container(
      color: Colors.white,
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: _controller,
              onSubmitted: _sendMessage,
              textInputAction: TextInputAction.send,
              decoration: const InputDecoration(
                hintText: 'Type your message...',
                border: OutlineInputBorder(
                    borderRadius: BorderRadius.all(Radius.circular(12))),
                contentPadding:
                    EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                isDense: true,
              ),
              style: const TextStyle(fontSize: 16),
              minLines: 1,
              maxLines: 4,
            ),
          ),
          const SizedBox(width: 6),
          IconButton(
            icon: const Icon(Icons.send, color: Colors.blueAccent),
            onPressed: () => _sendMessage(_controller.text),
            tooltip: 'Send',
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('AI Help Bot'),
        centerTitle: true,
        backgroundColor: Colors.white,
        foregroundColor: Colors.black,
        elevation: 1,
      ),
      body: SafeArea(
        child: Column(
          children: [
            Expanded(
              child: ListView.separated(
                controller: _scrollController,
                padding: const EdgeInsets.only(top: 12, bottom: 12),
                itemCount: _messages.length + (_isBotTyping ? 1 : 0),
                separatorBuilder: (_, __) => const SizedBox(height: 2),
                itemBuilder: (context, index) {
                  if (_isBotTyping && index == _messages.length) {
                    return _buildTypingIndicator();
                  }
                  return _buildMessageBubble(_messages[index]);
                },
              ),
            ),
            const Divider(height: 1, thickness: 1),
            _buildInputBar(),
          ],
        ),
      ),
    );
  }
}
