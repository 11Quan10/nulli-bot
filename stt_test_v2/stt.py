import asyncio
import discord
from discord.ext import commands, voice_recv
from discord.ext.voice_recv import AudioSink, VoiceData
from discord.opus import Decoder as OpusDecoder
import wave
from dotenv import load_dotenv
import os

bot = commands.Bot(command_prefix='$', intents=discord.Intents.all())

# Directory to store per-user recordings
RECORDING_DIR = "recordings"
os.makedirs(RECORDING_DIR, exist_ok=True)

class PerUserWaveSink(AudioSink):
    """Custom sink that writes separate .wav files for each speaking user."""
    CHANNELS = OpusDecoder.CHANNELS
    SAMPLE_WIDTH = OpusDecoder.SAMPLE_SIZE // CHANNELS
    SAMPLING_RATE = OpusDecoder.SAMPLING_RATE

    def __init__(self):
        super().__init__()
        self.user_files = {}

    def wants_opus(self) -> bool:
        return False  # we want PCM, not opus

    def write(self, user: discord.User, data: VoiceData) -> None:
        if user.id not in self.user_files:
            # New user detected; create a new wav file
            filename = os.path.join(RECORDING_DIR, f"{user.id}-recording.wav")
            wf = wave.open(filename, "wb")
            wf.setnchannels(self.CHANNELS)
            wf.setsampwidth(self.SAMPLE_WIDTH)
            wf.setframerate(self.SAMPLING_RATE)
            self.user_files[user.id] = wf

        self.user_files[user.id].writeframes(data.pcm)

    def cleanup(self):
        # Finalize all .wav files
        for wf in list(self.user_files.values()):
            try:
                wf.close()
            except Exception as e:
                print(f"Error closing file: {e}")
        self.user_files.clear()

@bot.command()
async def join(ctx):
    if ctx.author.voice:
        vc = await ctx.author.voice.channel.connect(cls=voice_recv.VoiceRecvClient)
        await ctx.send("Joined the voice channel.")

@bot.command()
async def record(ctx):
    vc: voice_recv.VoiceRecvClient = ctx.voice_client
    if not vc:
        await ctx.send("I'm not in a voice channel!")
        return

    sink = PerUserWaveSink()
    vc.listen(sink)

    await ctx.send("Recording for 10 seconds...")
    await asyncio.sleep(10)

    vc.stop()
    sink.cleanup()
    await ctx.send(f"Saved recordings to `{RECORDING_DIR}/`")

@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("Left the voice channel.")

@bot.command()
async def quit(ctx):
    await ctx.bot.close()

@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    await bot.process_commands(message)

load_dotenv()
token = os.getenv("DISCORD_BOT_TOKEN")
bot.run(token)