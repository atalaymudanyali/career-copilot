---
id: ai-voicebot
title: AI Voice Assistant
tech: [C#, ASP.NET Core, GPT-4, Whisper, TTS, WebSocket]
date: 2024
---

Production voice assistant integrating OpenAI GPT-4, Whisper speech-to-text, and text-to-speech APIs. Reduced end-to-end response latency from 10 seconds to 2-5 seconds through streaming architecture and parallel API orchestration.

Key technical decisions: streaming TTS delivery so users hear responses before full generation completes, WebSocket-based real-time communication, and a prompt engineering framework for multi-turn conversation context management.
