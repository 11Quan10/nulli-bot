# -*- coding: utf-8 -*-

import asyncio
import discord
from discord.ext import commands, voice_recv
from dotenv import load_dotenv
import logging
import os
import speech_recognition as sr
from typing import Any, Callable, Optional
import whisper
from faster_whisper import WhisperModel
import tempfile

# Initialize the model with desired parameters
model = WhisperModel("whisper-turbo-ct2", device="cuda", compute_type="float32", local_files_only=True)  # Use "cpu" if CUDA is unavailable

discord.opus._load_default()

bot = commands.Bot(command_prefix="$", intents=discord.Intents.all())
log = logging.getLogger(__name__)

SRProcessDataCB = Callable[[sr.Recognizer, sr.AudioData, discord.User], Optional[str]]
SRTextCB = Callable[[discord.User, str], Any]

class MySink(voice_recv.extras.SpeechRecognitionSink):
    def get_default_process_callback(self) -> SRProcessDataCB:
        def cb(recognizer: sr.Recognizer, audio: sr.AudioData, user: Optional[discord.User]) -> Optional[str]:
            # log.debug("Got %s, %s, %s", audio, audio.sample_rate, audio.sample_width)
            # text: Optional[str] = None
            # try:
            #     if self.default_recognizer == 'whisper':
            #         text = recognizer.recognize_whisper(
            #             audio,
            #             model="small",       # change to "tiny", "base", "medium", "large" as needed
            #             language="en"        # force English
            #         )
            #     else:
            #         print(type(self.default_recognizer))
            #         func = getattr(recognizer, 'recognize_' + self.default_recognizer, recognizer.recognize_google)  # type: ignore
            #         text = func(audio)  # type: ignore
            # except sr.UnknownValueError:
            #     log.debug("Bad speech chunk")
            #     # self._debug_audio_chunk(audio)

            # return text

            try:
                # Create a temporary WAV file from the AudioData
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
                    temp_wav.write(audio.get_wav_data())
                    temp_wav_path = temp_wav.name

                # Transcribe the audio using faster-whisper
                segments, _ = model.transcribe(temp_wav_path, language="en", beam_size=5)

                # Combine transcribed segments into a single string
                transcription = " ".join(segment.text for segment in segments)

                return transcription.strip()

            except Exception as e:
                log.exception("Error during transcription: %s", e)
                return None

            finally:
                # Clean up the temporary file
                if os.path.exists(temp_wav_path):
                    os.remove(temp_wav_path)

        return cb
    
    # def get_default_text_callback(self) -> SRTextCB:
    #     def cb(user: Optional[discord.User], text: Optional[str]) -> Any:
    #         log.info("%s said: %s", user.display_name if user else 'Someone', text)

    #     return cb

class Testing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def test(self, ctx):

        vc = await ctx.author.voice.channel.connect(cls=voice_recv.VoiceRecvClient)
        vc.listen(MySink(default_recognizer='whisper'))

    @commands.command()
    async def stop(self, ctx):
        await ctx.voice_client.disconnect()

    @commands.command()
    async def die(self, ctx):
        ctx.voice_client.stop()
        await ctx.bot.close()

@bot.event
async def on_ready():
    print('Logged in as {0.id}/{0}'.format(bot.user))
    print('------')

@bot.event
async def setup_hook():
    await bot.add_cog(Testing(bot))

load_dotenv()
token = os.getenv("DISCORD_BOT_TOKEN")
bot.run(token)