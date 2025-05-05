import asyncio
from audiosub import AudioSub
from kokoro import KPipeline
import soundfile as sf
import pyrubberband as pyrb
import torch
import discord
from discord.ext import commands
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage

import os

from graph.graph import Graph

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="$", intents=intents)

# start with one channel for now
# connections = {}
connections = {}
can_speak = {}

model = ChatOllama(model="llama3.2:3b", temperature=0.5)

# load kokoro voice
pipeline = KPipeline(lang_code="a", device="cpu")
audio_root = "./audio"
if not os.path.exists(audio_root):
    os.makedirs(audio_root)


load_dotenv()
token = os.getenv("DISCORD_BOT_TOKEN")

graph = Graph()


@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    await bot.process_commands(message)


# COMMANDS


@bot.command()
async def join(ctx: commands.Context):
    channel = ctx.author.voice.channel
    if channel is None:
        await ctx.send("join a vc first")
        return
    connections[ctx.guild.id] = await channel.connect()
    can_speak[ctx.guild.id] = True


@bot.command()
async def leave(ctx: commands.Context):
    if ctx.voice_client is not None:
        await ctx.voice_client.disconnect()
        del connections[ctx.guild.id]
        del can_speak[ctx.guild.id]


@bot.command()
async def filter(ctx: commands.Context):
    await filter_speak(ctx)


@bot.command()
async def invoke(ctx: commands.Context, *, text: str):
    response = await graph.invoke_model_with_human_messages(
        [HumanMessage(content=f"{ctx.author.name}: {text}")],
        _vclient=connections[ctx.guild.id],
        _tts_callback=speak,
        _stop_audio_callback=filter_speak,
    )
    # await ctx.send(response["response"])
    print(response["response"])
    for message in response["messages"]:
        message.pretty_print()
    await ctx.send("response sent")


# SERVICE FUNCTIONS
async def play_audio(vclient, filename: str):
    src = discord.FFmpegPCMAudio(source=filename, executable="ffmpeg.exe")
    vclient.play(src)

    while vclient.is_playing():
        await asyncio.sleep(0.1)


async def text_to_audio_segments(text: str):
    rate = 24000
    generator = pipeline(text, voice="af_heart")
    for i, (gs, ps, audio) in enumerate(generator):
        max_i = i
        audio = audio.numpy()
        audio = pyrb.time_stretch(audio, rate, 0.95)
        audio = pyrb.pitch_shift(audio, rate, n_steps=3)
        sf.write(f"{audio_root}/{i}.wav", audio, rate)
    return max_i


async def speak(ctx, text: str):
    i = await text_to_audio_segments(text)
    for j in range(i + 1):
        if not can_speak[ctx.guild.id]:
            break
        await play_audio(connections[ctx.guild.id], f"{audio_root}/{j}.wav")
    if not can_speak[ctx.guild.id]:
        i = await text_to_audio_segments("Filtered")
        for j in range(i + 1):
            await play_audio(connections[ctx.guild.id], f"{audio_root}/{j}.wav")
        can_speak[ctx.guild.id] = True


async def filter_speak(ctx):
    vclient = connections[ctx.guild.id]
    can_speak[ctx.guild.id] = False
    if vclient.is_playing():
        vclient.stop()


bot.run(token)
