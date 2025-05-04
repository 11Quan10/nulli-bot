# quadbot
Authors: Adrian Munoz, Daniel Nguyen, Quan Pham \
For our NLP project, we'll be creating a discord assistant bot with various features. Our goal is to have the bot act as a regular user that can join in on conversations without any sense of awkwardness.

# WIP
## Progress
Current functionalities:
* Bot can join and leave voice channels
* When prompted, the bot can answer/reply to users using an LLM (Ollama)
* Bot can play locally saved audio files
* Bot can record audio from users in voice channel and send the audio as a message file and/or save it locally
* Using a locally saved audio file, bot can transcript it into text using OpenAI Whisper and send the transcription as a message

## How to set up
Please view `requirements.txt` for list of dependencies.
Main libraries being used: pycord, whisper, langchain_ollama, SpeechRecognition


COMPILE THIS INTO A REQUIREMENTS.TXT LATER

```bash
pip install discord.py[voice]
pip install discord-ext-voice-recv
pip install python-dotenv langchain langgraph langsmith langchain_ollama langchain-text-splitters langchain-community langchain_elasticsearch

pip install -qU langchain-qdrant
pip install fastembed

pip install -qU duckduckgo-search langchain-community

pip install insanely-fast-whisper --ignore-requires-python
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install --upgrade transformers optimum accelerate
pip install -q kokoro>=0.9.4 soundfile
# for japanese
pip install misaki[ja]
python -m unidic download
download ffmpeg https://www.gyan.dev/ffmpeg/builds/ and configure the PATH variable to /bin
download rubberband https://breakfastquay.com/rubberband/ and configue the PATH variable to extracted zip folder (contains rubberband.exe)
pip install pyrubberband


```

Have Docker installed
curl -fsSL https://elastic.co/start-local | sh

