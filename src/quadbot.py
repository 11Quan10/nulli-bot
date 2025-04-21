import asyncio
from audiosub import AudioSub
import discord
from discord.ext import commands
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
import os


discord.opus._load_default()
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="$", intents=intents)
model = ChatOllama(model="llama3.2:3b", temperature=0.5)
connections = {}


@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")


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
    print(f"{ctx.author} invoked the chatai command with prompt: {prompt}")

    response = model.invoke(prompt).content

    # split messages into chunks of 2000 characters
    chunks = [response[i : i + 2000] for i in range(0, len(response), 2000)]
    for chunk in chunks:
        await ctx.send(chunk)


@bot.command()
async def fart(ctx: commands.Context):
    print(f"{ctx.author} invoked the fart command")
    await ctx.send(f"{ctx.author.mention} farted! 💨")  # sends a message in the channel where the command was invoked


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
async def talk(ctx, *, message: str):
    AS = AudioSub("assets")
    AS.text_to_speech(message, "temp")
    await play(ctx, "temp")


@bot.command()
async def play(ctx, file: str):
    vchannel = ctx.author.voice.channel
    if vchannel is None:
        await ctx.send("You need to be in a voice channel to play audio.")
        return

    audio_src = "assets\\" + file + ".wav"
    if not os.path.exists(audio_src):
        await ctx.send(f"Audio file '{file}' not found.")
        return

    await play_audio(vchannel, audio_src)


async def play_audio(vchannel, filename: str):
    vclient = await vchannel.connect()

    src = discord.FFmpegPCMAudio(source=filename)
    vclient.play(src)

    while vclient.is_playing():
        await asyncio.sleep(0.1)
    await vclient.disconnect()


@bot.command()
async def record(ctx):  # If you're using commands.Bot, this will also work.
    voice = ctx.author.voice

    if not voice:
        await ctx.send("You aren't in a voice channel!")

    vc = await voice.channel.connect()  # Connect to the voice channel the author is in.
    connections.update({ctx.guild.id: vc})  # Updating the cache with the guild and channel.

    vc.start_recording(
        discord.sinks.WaveSink(),  # The sink type to use.
        once_done,  # What to do once done.
        ctx.channel,  # The channel to disconnect from.
    )
    await ctx.send("Started recording!")


async def once_done(
    sink: discord.sinks, channel: discord.TextChannel, *args
):  # Our voice client already passes these in.
    recorded_users = [  # A list of recorded users
        f"<@{user_id}>" for user_id, audio in sink.audio_data.items()
    ]

    await sink.vc.disconnect()  # Disconnect from the voice channel.
    files = [
        discord.File(audio.file, f"{user_id}.{sink.encoding}") for user_id, audio in sink.audio_data.items()
    ]  # List down the files.

    for user_id, audio in sink.audio_data.items():
        with open(f"assets\\{user_id}-output.wav", "wb") as f:  # Open the recorded audio file.
            f.write(audio.file.getbuffer())  # Write the audio data to the file.

    await channel.send(
        f"finished recording audio for: {', '.join(recorded_users)}.", files=files
    )  # Send a message with the accumulated files.
    AS = AudioSub("assets")  # Create an instance of AudioSub with the directory where audio files are stored.
    await channel.send(AS.transcribe())

    # # delete files in assets directory
    # for file in os.listdir("assets"):
    #     if file.endswith(".wav"):
    #         os.remove(os.path.join("assets", file))


@bot.command()
async def stop_recording(ctx):
    if ctx.guild.id in connections:  # Check if the guild is in the cache.
        vc = connections[ctx.guild.id]
        vc.stop_recording()  # Stop recording, and call the callback (once_done).
        del connections[ctx.guild.id]  # Remove the guild from the cache.
        await ctx.message.delete()  # And delete.
    else:
        await ctx.send("I am currently not recording here.")  # Respond with this if we aren't recording.

# this is a proof of concept
@bot.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    if member.id == bot.user.id:
        return
    if before.channel is None and after.channel is not None:
        if after.channel.id in [vc.channel.id for vc in bot.voice_clients]:
            AS = AudioSub("assets")
            AS.text_to_speech(f"Hi there {member.name}", "temp")
            audio_src = "assets\\" + "temp" + ".wav"
            vclient = filter(lambda vc: vc.channel.id == after.channel.id, bot.voice_clients)
            vclient = list(vclient)[0] if vclient else None
            src = discord.FFmpegPCMAudio(source=audio_src)
            vclient.play(src)
            while vclient.is_playing():
                await asyncio.sleep(0.1)


load_dotenv()
token = os.getenv("DISCORD_BOT_TOKEN")
bot.run(token)
