import discord
from langchain_ollama import ChatOllama
import random

# shows = ["Sousou no Frieren", "Fullmetal Alchemist: Brotherhood", "Steins;Gate", "Shingeki no Kyojin", "Gintama", "Hunter x Hunter", "Bleach",
#          "Kaguya-sama wa Kokurasetai", "Fruits Basket", "Clannad", "3-Gatsu no Lion", "Code Geass", "Monster", "Ore dake Level Up na Ken", "Kingdom",
#          "Vinland Saga", "Mob Psycho", "Hajime no Ippo", "Haikyuu!", "Bocchi the Rock!", "Jujutsu Kaisen", "Oshi no Ko", "Tokyo Revengers", "Tokyo Ghoul", "Naruto",
#          "One Piece", "Death Note", "Demon Slayer", "My Hero Academia", "Chainsaw Man", "86", "Violet Evergarden", "Made in Abyss", "Re:Zero", "Dragon Ball Z",
#          "Cowboy Bebop", "Samurai Champloo", "Neon Genesis Evangelion", "Your Lie in April", "Anohana", "The Promised Neverland", "Paranoia Agent", "Serial Experiments Lain",
#          "The Rising of the Shield Hero"]

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
model = ChatOllama(model="llama3.2:3b", temperature=0.5)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$chatai'):
        response = model.invoke(message.content[8:].strip()).content

        # split messages into chunks of 2000 characters
        # however, this does cause problems with text formatting via markdown (maybe fix this later?)
        chunks = [response[i:i+2000] for i in range(0, len(response), 2000)]
        for chunk in chunks:
            await message.channel.send(chunk)

client.run('__BOT_TOKEN__')