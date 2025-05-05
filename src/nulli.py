import asyncio
from audio_tools import AudioTools
import codecs
import re
import torch
import discord
from discord.ext import commands, voice_recv
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
import os
from graph.graph import Graph
import warnings

warnings.filterwarnings("ignore")

load_dotenv()
token = os.getenv("DISCORD_BOT_TOKEN")

# load discord defaults
discord.opus._load_default()
bot = commands.Bot(command_prefix="$", intents=discord.Intents.all())

audio_tools = AudioTools()

# load filtered words from encrypted txt
if os.path.exists("bad_words.txt"):
    with open("bad_words.txt", "r") as file:
        content = codecs.encode(file.read(), "rot13")
    filtered_words = [word.strip() for word in content.split(",")]
    filter_pattern = re.compile(r"\b(" + "|".join(filtered_words) + r")\b", flags=re.IGNORECASE)
else:
    filter_pattern = re.compile(r"(?!)")

# graph = Graph()

# initialize per-server variables
connections = {}
can_speak = {}


@bot.event
async def on_ready():
    print("Logged in as {0.id}/{0}".format(bot.user))


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
    connections[ctx.guild.id] = await channel.connect(cls=voice_recv.VoiceRecvClient)
    connections[ctx.guild.id].listen(audio_tools.StreamSink(audio_tools))
    can_speak[ctx.guild.id] = True


@bot.command()
async def leave(ctx: commands.Context):
    if ctx.voice_client is not None:
        ctx.voice_client.stop()
        await ctx.bot.close()
        await ctx.voice_client.disconnect()
        del connections[ctx.guild.id]
        del can_speak[ctx.guild.id]


@bot.command()
async def filter(ctx: commands.Context):
    await filter_speak(ctx)


@bot.command()
async def invoke(ctx: commands.Context, *, text: str):
    # response = await graph.invoke_model_with_human_messages(
    #     [HumanMessage(content=f"{ctx.author.name}: {text}")],
    #     _ctx=ctx,
    #     _tts_callback=speak,
    #     _stop_audio_callback=filter_speak,
    # )
    # print(response["response"])
    # for message in response["messages"]:
    #     message.pretty_print()
    await ctx.send("response sent")


# SERVICE FUNCTIONS
async def play_audio(vclient, filename: str):
    src = discord.FFmpegPCMAudio(source=filename, executable="ffmpeg.exe")
    vclient.play(src)

    while vclient.is_playing():
        await asyncio.sleep(0.1)


async def filter_regex(text: str):
    match = filter_pattern.search(text)
    if match:
        return match.group()
    return None


async def speak(ctx, text: str):
    i = await audio_tools.text_to_speech(text)
    for j in range(i + 1):
        if not can_speak[ctx.guild.id]:
            break
        await play_audio(connections[ctx.guild.id], f"{audio_tools.audio_root}/{j}.wav")
    if not can_speak[ctx.guild.id]:
        i = await audio_tools.text_to_speech("Filtered")
        for j in range(i + 1):
            await play_audio(connections[ctx.guild.id], f"{audio_tools.audio_root}/{j}.wav")
        can_speak[ctx.guild.id] = True


async def filter_speak(ctx):
    vclient = connections[ctx.guild.id]
    can_speak[ctx.guild.id] = False
    if vclient.is_playing():
        vclient.stop()


bot.run(token)
