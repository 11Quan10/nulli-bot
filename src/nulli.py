import asyncio
import re
import time
from typing import Dict, TypedDict
from audio_tools import AudioTools, WaveSinkMultipleUsers
from discord.ext.voice_recv import SilenceGeneratorSink
import torch
import discord
from discord.ext import commands, voice_recv
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
import os
from graph.graph import Graph
import warnings
from pydub import AudioSegment

warnings.filterwarnings("ignore")
load_dotenv()
token = os.getenv("DISCORD_BOT_TOKEN")

# load discord defaults
discord.opus._load_default()
bot = commands.Bot(command_prefix="$", intents=discord.Intents.all())

audio_tools = AudioTools()

graph = Graph()


class Connection(TypedDict):
    ctx_guild_id: int
    voice_client: voice_recv.VoiceRecvClient
    can_speak: bool
    connection_flag: bool
    start_time_no_one_speaking: int
    audio_tempfile: str
    responding: bool


# initialize per-server variables
connections: Dict[int, Connection] = {}


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
async def talk(ctx: commands.Context, *, text: str):
    await speak(ctx, text)


@bot.command()
async def join(ctx: commands.Context):
    channel = ctx.author.voice.channel
    if channel is None:
        await ctx.send("join a vc first")
        return
    vclient = await channel.connect(cls=voice_recv.VoiceRecvClient)
    if not os.path.exists(f"{audio_tools.audio_root}/{ctx.guild.id}"):
        os.makedirs(f"{audio_tools.audio_root}/{ctx.guild.id}")
    connections[ctx.guild.id] = Connection(
        ctx_guild_id=ctx.guild.id,
        voice_client=vclient,
        connection_flag=True,
        can_speak=True,
        start_time_no_one_speaking=-1,
        audio_tempfile=f"{audio_tools.audio_root}/{ctx.guild.id}",
        responding=False,
    )

    connections[ctx.guild.id]["voice_client"].listen(
        SilenceGeneratorSink(WaveSinkMultipleUsers(connections[ctx.guild.id]["audio_tempfile"]))
    )

    asyncio.create_task(connection_event_loop(connections[ctx.guild.id]))


@bot.command()
async def leave(ctx: commands.Context):
    if ctx.voice_client is not None:
        connections[ctx.guild.id]["voice_client"].stop_listening()
        connections[ctx.guild.id]["voice_client"].stop()
        connections[ctx.guild.id]["voice_client"].cleanup()
        connections[ctx.guild.id]["voice_client"].disconnect()
        if os.path.exists(connections[ctx.guild.id]["audio_tempfile"]):
            os.removedirs(connections[ctx.guild.id]["audio_tempfile"])
        del connections[ctx.guild.id]


# EVENT LOOP


async def connection_event_loop(connection: Connection):
    while True:
        if connection["connection_flag"] is False:
            break
        print("Checking for speaking users...")
        speaking_flag = False
        for member in connection["voice_client"].channel.members:
            if connection["voice_client"].get_speaking(member):
                speaking_flag = True
        if speaking_flag is False:
            if connection["start_time_no_one_speaking"] == -1:
                connection["start_time_no_one_speaking"] = time.time()
            elif time.time() - connection["start_time_no_one_speaking"] > 5:
                connection["responding"] = True
                user_list = connection["voice_client"].channel.members
                users_audio_files = {}
                for member in user_list:
                    if os.path.exists(f"{connection['audio_tempfile']}/{member.name}.wav"):
                        users_audio_files[member.name] = f"{connection['audio_tempfile']}/{member.name}.wav"
                print("Processing audio files...")
                processed_transcriptions = await process_audio_batch(users_audio_files=users_audio_files)
                print("Responding...")
                await invoke(
                    ctx_guild_id=connection["ctx_guild_id"],
                    messages=[HumanMessage(content=f"{chunk[0]}: {chunk[2]}") for chunk in processed_transcriptions],
                )
                connection["start_time_no_one_speaking"] = -1
                connection["responding"] = False
        await asyncio.sleep(2)


async def process_audio_batch(users_audio_files):
    # need to make all audio files the same length
    max_frame_size = 0
    file_corrupted_users = []
    for user in users_audio_files.keys():
        try:  # file may be corrupted
            audio = AudioSegment.from_file(users_audio_files[user], format="wav")
        except Exception as e:
            file_corrupted_users.append(user)
            continue
        if len(audio) > max_frame_size:
            max_frame_size = len(audio)
    for user in file_corrupted_users:
        del users_audio_files[user]
    for file in users_audio_files.values():
        await audio_tools.prepend_silence(file, max_frame_size - len(AudioSegment.from_file(file, format="wav")), file)
    user_transcriptions_full = {}
    for user in users_audio_files.keys():
        user_transcriptions_full[user] = await audio_tools.transcribe(users_audio_files[user])
    #  combines all chunks into a single list of tuples (user, timestamp, text)
    chunks = [
        (user, chunk["timestamp"][0], chunk["text"])
        for user in user_transcriptions_full.keys()
        for chunk in user_transcriptions_full[user]["chunks"]
    ]
    # sort the chunks by timestamp
    chunks.sort(key=lambda x: x[1])
    # regex to replace mispoken words for "nulli"
    for i in range(len(chunks)):
        chunks[i] = (
            chunks[i][0],
            chunks[i][1],
            re.sub(r"\b(?:N[uo]l{1,2}[iey\-]{1,3})\b", "Nulli", chunks[i][2], flags=re.IGNORECASE),
        )

    return chunks


# SERVICE FUNCTIONS


async def invoke(ctx_guild_id, messages: list[HumanMessage]):
    response = await graph.invoke_model_with_human_messages(
        messages=messages,
        _ctx_guild_id=ctx_guild_id,
        _tts_callback=speak,
        _stop_audio_callback=filter_speak,
    )
    print(response["response"])
    for message in messages:
        message.pretty_print()


async def play_audio(vclient, filename: str):
    src = discord.FFmpegPCMAudio(source=filename, executable="ffmpeg")
    vclient.play(src)

    while vclient.is_playing():
        await asyncio.sleep(0.1)


async def speak(ctx_guild_id: int, text: str):
    print("Speaking...")
    i = await audio_tools.text_to_speech(text)
    print(f"{audio_tools.audio_root}/{i}.wav")
    print(connections[ctx_guild_id]["can_speak"])
    for j in range(i + 1):
        if not connections[ctx_guild_id]["can_speak"]:
            break
        await play_audio(connections[ctx_guild_id]["voice_client"], f"{audio_tools.audio_root}/{j}.wav")
    if not connections[ctx_guild_id]["can_speak"]:
        i = await audio_tools.text_to_speech("Filtered")
        for j in range(i + 1):
            await play_audio(connections[ctx_guild_id]["voice_client"], f"{audio_tools.audio_root}/{j}.wav")
        connections[ctx_guild_id]["can_speak"] = True


async def filter_speak(ctx_guild_id):
    vclient = connections[ctx_guild_id]["voice_client"]
    connections[ctx_guild_id]["can_speak"] = False
    if vclient.is_playing():
        vclient.stop()
    return None


bot.run(token)
