import asyncio
from audiosub_fork import AudioSub
from kokoro import KPipeline
import soundfile as sf
import pyrubberband as pyrb
import torch
import discord
from discord.ext import commands
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
import os
import numpy as np
import datetime, wave, io

discord.opus._load_default()
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix = "$", intents=intents)
model = ChatOllama(model="llama3.2:3b", temperature=0.5)
connections = {}

#load kokoro voice
pipeline = KPipeline(lang_code='a')

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    await bot.process_commands(message)

@bot.command()
async def chatai(ctx: commands.Context, *, prompt: str):
    """
    Responds to a prompt using the ChatOllama model.
    Usage: $chatai <your prompt here>
    """
    print(f'{ctx.author} invoked the chatai command with prompt: {prompt}')
    
    response = model.invoke(prompt).content

    # split messages into chunks of 2000 characters
    chunks = [response[i:i+2000] for i in range(0, len(response), 2000)]
    for chunk in chunks:
        await ctx.send(chunk)

@bot.command()
async def fart(ctx: commands.Context):
    print(f'{ctx.author} invoked the fart command')
    await ctx.send(f'{ctx.author.mention} farted! 💨') # sends a message in the channel where the command was invoked


@bot.command()
async def join(ctx):
    channel = ctx.author.voice.channel
    if channel is None:
        await ctx.send("join a vc first")
        return
    await channel.connect()

@bot.command()
async def leave(ctx):
    if ctx.voice_client is not None:
        await ctx.voice_client.disconnect()
        

@bot.command()
async def play(ctx, file: str):
    vchannel = ctx.author.voice.channel
    if vchannel is None:
        await ctx.send("You need to be in a voice channel to play audio.")
        return
    
    audio_src = "assets\\" + file + ".mp3"
    if not os.path.exists(audio_src):
        await ctx.send(f"Audio file '{file}' not found.")
        return
    
    await play_audio(vchannel, audio_src)

async def play_audio(vchannel, filename: str):
    vclient = await vchannel.connect()

    src = discord.FFmpegPCMAudio(source=filename, executable='ffmpeg.exe')
    vclient.play(src)
    
    while vclient.is_playing():
        await asyncio.sleep(.1)
    await vclient.disconnect()


@bot.command()
async def record(ctx):  # If you're using commands.Bot, this will also work.
    voice = ctx.author.voice

    if not voice:
        await ctx.send("You aren't in a voice channel!")
        return

    vc: discord.VoiceClient = ctx.voice_client
    if not vc or vc is None:
        vc: discord.VoiceClient = await voice.channel.connect()

    connections.update({ctx.guild.id: vc})  # Updating the cache with the guild and channel.

    vc.start_recording(
        discord.sinks.WaveSink(),  # The sink type to use.
        finished_callback,  # What to do once done.
        ctx.channel,  # The channel to disconnect from.
        sync_start=False
    )

    async def monitor_audio():
        global is_speaking
        is_speaking = True
        prev_file_size = 0
        was_speaking = False
        while vc.recording:
            for user_id, audio_data in vc.sink.audio_data.items():
                curr_file_size = audio_data.file.tell()

                if curr_file_size > prev_file_size:
                    is_speaking = True
                    was_speaking = True
                    prev_file_size = audio_data.file.tell()
                else:
                    is_speaking = False

                # print("is_speaking:", is_speaking)
                await ctx.send(f"Somebody is speaking (guess): {is_speaking}")

                # When user stops speaking, export the audio segment to a file
                if not is_speaking and was_speaking:
                    was_speaking = False

                    # Extract the audio segment
                    audio_data.file.seek(0)  # Go to the beginning of the file
                    data_to_write = audio_data.file.read()  # Read the entire content

                    # Write the audio segment to a file
                    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
                    filename = f"..\\assets\\{user_id}_{timestamp}-output.wav"
                    with wave.open(filename, 'wb') as wf:
                        wf.setnchannels(2)  # Set the number of channels
                        wf.setsampwidth(2)  # Set the sample width (in bytes)
                        wf.setframerate(24000)  # Set the frame rate (samples per second)
                        wf.writeframes(data_to_write)

                    # AS = AudioSub()  # Create an instance of AudioSub with the directory where audio files are stored.
                    # await ctx.send(f"<@{user_id}> said: \"{AS.transcribe(filename)}\"")
                    # await asyncio.sleep(0.2)
                    # os.remove(filename)
                    
                    # Reset the BytesIO object for the next speech segment
                    audio_data.file = io.BytesIO()
                    prev_file_size = 0
                
            await asyncio.sleep(3)  # Adjust the interval as needed

    bot.loop.create_task(monitor_audio())
    await ctx.send("Started!")

async def finished_callback(sink: discord.sinks.WaveSink, channel: discord.TextChannel):
    asyncio.run_coroutine_threadsafe(channel.send("Recording finished!"), bot.loop)
    global is_speaking
    is_speaking = False
    print("Recording finished, no more audio frames detected.")
    await channel.send("Recording finished, no more audio frames detected.")
    
@bot.command()
async def stop_recording(ctx):
    if ctx.guild.id in connections:  # Check if the guild is in the cache.
        vc = connections[ctx.guild.id]
        vc.stop_recording()  # Stop recording, and call the callback (once_done).
        del connections[ctx.guild.id]  # Remove the guild from the cache.
        await ctx.message.delete()  # And delete.
        await ctx.send("Recording has ended!")
    else:
        await ctx.send("I am currently not recording here.")  # Respond with this if we aren't recording.


async def speak(text: str):
    rate = 24000
    generator = pipeline(text, voice='af_heart')
    for i, (gs, ps, audio) in enumerate(generator):
        max_i = i
        print(i)
        audio = audio.numpy()
        audio = pyrb.time_stretch(audio, rate, 0.95)
        audio = pyrb.pitch_shift(audio, rate, n_steps=3)
        sf.write(f'{i}.wav', audio, rate)
    return max_i


@bot.command()
async def test_speak(ctx, text: str):
    vchannel = ctx.author.voice.channel

    i = await speak(text)
    for j in range(i+1):
        await play_audio(vchannel, f'{j}.wav')



load_dotenv()
token = os.getenv('DISCORD_BOT_TOKEN')
bot.run(token)