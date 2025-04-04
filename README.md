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
