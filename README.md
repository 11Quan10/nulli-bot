# 🌸 Nulli QuAD Bot

> A Discord-native AI assistant that blends seamlessly into voice chats — no awkward bots allowed.

<p align="center">
  <img src="./assets/nulli.png" alt="Nulli Icon" width="120" height="120">
</p>

---

## ✨ Project Overview

**Authors:** Adrian Munoz, Daniel Nguyen, Quan Pham

Nulli is an AI-powered Discord bot built for natural, real-time voice interaction. Designed for seamless integration into group calls, Nulli can speak, listen, transcribe, and even learn over time — all while feeling like just another user in the chat.

---

## 🚀 Features

- 🎙️ Joins and leaves voice channels  
- 💬 Responds using a locally served LLM (via [Ollama](https://ollama.com/))  
- 🔊 Plays local audio files  
- 📼 Records user audio and sends/stores it  
- 📝 Transcribes audio using OpenAI Whisper  
- 🧠 Built with LangChain, LangGraph, and Qdrant for RAG capabilities  

---

## 💾 Developer Setup

### 📦 Requirements

> **Python:** 3.11.0rc2  
> Be sure to configure your environment variables and dependencies as shown below.

#### 🔧 Core Dependencies

```bash
pip install python-dotenv
pip install discord.py[voice]
pip install discord-ext-voice-recv
```

#### 🧠 LLM + RAG Stack

```bash
pip install langchain langgraph langsmith langchain-community
pip install langchain_ollama
pip install langchain-qdrant fastembed
pip install duckduckgo-search
```

#### 🗣️ Speech-To-Text

> Download [ffmpeg](https://www.gyan.dev/ffmpeg/builds/) and add it to your PATH.

```bash
pip install SpeechRecognition
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install --upgrade transformers optimum accelerate
pip install deepfilternet
```

#### 🗨️ Text-To-Speech

> Download [rubberband](https://breakfastquay.com/rubberband/) and add it to your PATH.

```bash
pip install -q "kokoro>=0.9.4" soundfile
pip install pyrubberband
pip install misaki[ja]
python -m unidic download
```

#### 🦥 Finetuning (Unsloth)

> Follow the setup at [Unsloth Docs](https://docs.unsloth.ai/get-started/installing-+-updating)

```bash
pip install "unsloth[windows] @ git+https://github.com/unslothai/unsloth.git"
```

---

### ⚙️ Environment Configuration

Create a `.env` file in `src/`:

```env
DISCORD_BOT_TOKEN=your_token
LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT=your_endpoint
LANGSMITH_API_KEY=your_api_key
LANGSMITH_PROJECT=your_project_name
PROJECT_ROOT=/absolute/path/to/src
```

---

## 🖥️ Running Locally

### 🦙 Start Ollama

Run Ollama on multiple ports to reduce cold starts:

```bash
# Terminal 1
OLLAMA_HOST=localhost:11434 OLLAMA_NUM_PARALLEL=2 OLLAMA_KEEP_ALIVE=-1 OLLAMA_FLASH_ATTENTION=1 ollama serve

# Terminal 2
OLLAMA_HOST=localhost:11435 OLLAMA_KEEP_ALIVE=-1 OLLAMA_FLASH_ATTENTION=1 ollama serve

# Terminal 3
OLLAMA_HOST=localhost:11436 OLLAMA_KEEP_ALIVE=-1 OLLAMA_FLASH_ATTENTION=1 ollama serve
```

### 🌸 Start Nulli

Make sure you've invited Nulli to your Discord server. Then, from `src/`:

```bash
python nulli.py
```

---

## 💬 Supported Discord Commands

| Command | Description |
| - | - |
| `$join` | Joins the current voice channel and starts the conversational loop |
| `$leave` | Leaves the current voice channel |

---
