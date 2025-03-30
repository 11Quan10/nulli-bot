import asyncio
import discord
from discord.ext import commands, voice_recv
from langchain_ollama import ChatOllama
import os
import random

discord.opus._load_default()
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix = "$", intents=intents)
model = ChatOllama(model="llama3.2:3b", temperature=0.5)

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
    await channel.connect(cls=voice_recv.VoiceRecvClient)

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
    vclient = await vchannel.connect(cls=voice_recv.VoiceRecvClient)

    src = discord.FFmpegPCMAudio(source=filename, executable='C:\\ffmpeg-7.1.1-full_build\\ffmpeg-7.1.1-full_build\\bin\\ffmpeg.exe')
    vclient.play(src)
    
    while vclient.is_playing():
        await asyncio.sleep(.1)
    await vclient.disconnect()




@bot.command()
async def test(ctx):
    print("test")
    def callback(user, data: voice_recv.VoiceData):
        print(f"packet from {user}")
        
    vc = await ctx.author.voice.channel.connect(cls=voice_recv.VoiceRecvClient)
    vc.listen(voice_recv.BasicSink(callback))



bot.run('__BOT_TOKEN__')