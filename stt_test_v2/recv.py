# -*- coding: utf-8 -*-

import asyncio
import discord
from discord.ext import commands, voice_recv
from dotenv import load_dotenv
import logging
import os
import speech_recognition as sr
from typing import Any, Callable, Optional
import tempfile

from transformers import pipeline
from transformers.utils import is_flash_attn_2_available
import torch

# Initialize the model with desired parameters
# model = WhisperModel("whisper-turbo-ct2", device="cuda", compute_type="float32", local_files_only=True)  # Use "cpu" if CUDA is unavailable
pipe = pipeline(
    task="automatic-speech-recognition",
    model="openai/whisper-large-v3-turbo",        # check out more models at: https://huggingface.co/models?pipeline_tag=automatic-speech-recognition
    torch_dtype=torch.float32,
    device="cuda:0",  # or mps for Mac devices
    model_kwargs={"attn_implementation": "flash_attention_2"}
    if is_flash_attn_2_available()
    else {"attn_implementation": "sdpa"},
)

discord.opus._load_default()
bot = commands.Bot(command_prefix="$", intents=discord.Intents.all())
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s\t%(filename)s - %(message)s')

SRProcessDataCB = Callable[[sr.Recognizer, sr.AudioData, discord.User], Optional[str]]
SRTextCB = Callable[[discord.User, str], Any]

from pydub import AudioSegment
from df import enhance, init_df
from df.enhance import load_audio, save_audio
import warnings
warnings.filterwarnings("ignore")


model, df_state, _ = init_df()

def is_silent_dbfs(audio_data: sr.AudioData, dbfs_threshold: float = -45.0) -> bool:
    # Convert audio data to WAV for pydub
    sound = AudioSegment(
        data=audio_data.get_raw_data(),
        sample_width=audio_data.sample_width,
        frame_rate=audio_data.sample_rate,
        channels=1
    )
    return sound.dBFS < dbfs_threshold

class MySink(voice_recv.extras.SpeechRecognitionSink):
    def get_default_process_callback(self) -> SRProcessDataCB:
        def cb(recognizer: sr.Recognizer, audio: sr.AudioData, user: Optional[discord.User]) -> Optional[str]:
            if is_silent_dbfs(audio):
                return None

            try:
                # Create a temporary WAV file from the AudioData
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
                    temp_wav.write(audio.get_wav_data())
                    temp_wav_path = temp_wav.name
                audio, _ = load_audio(temp_wav_path, sr=df_state.sr())
                # Denoise the audio
                enhanced = enhance(model, df_state, audio)
                save_audio(temp_wav_path, enhanced, df_state.sr())

                if AudioSegment.from_file(temp_wav_path, format="wav").dBFS < -45.0:
                    print("Audio is silent, skipping transcription.")
                    return None

                # Transcribe the audio using Transformers Pipeline for ASR
                result = pipe(temp_wav_path, 
                              chunk_length_s=5, 
                              batch_size=24, 
                              return_timestamps=True,
                              max_new_tokens=256,
                              generate_kwargs={"language": "en"})
                return result["text"]

            except Exception as e:
                logging.exception("Error during transcription: %s", e)
                return None

            finally:
                # Clean up the temporary file
                if os.path.exists(temp_wav_path):
                    os.remove(temp_wav_path)

        return cb
    
    def get_default_text_callback(self) -> SRTextCB:
        def cb(user: Optional[discord.User], text: Optional[str]) -> Any:
            if text:
                logging.info("%s said: %s", user.display_name if user else 'Someone', text)

        return cb

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