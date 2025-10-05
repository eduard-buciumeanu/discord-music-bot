import os
import discord
from discord.ext import commands
from dotenv import load_dotenv


load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Define the necessary intents (default is enough for this utility)
intents = discord.Intents.default()

client = commands.Bot(command_prefix="!", intents=intents)

@client.event
async def on_ready():
    print(f"Logged in as {client.user} (ID: {client.user.id})")
    print("------")
    
    print("Clearing all global commands...")
    await client.tree.sync()
    print("Global commands cleared.")
    
    print("Clearing all guild-specific commands...")
    for guild in client.guilds:
        await client.tree.sync(guild=discord.Object(id=guild.id))
        print(f"Cleared commands for guild: {guild.name} (ID: {guild.id})")
    
    print("------")
    print("All commands have been successfully cleared.")
    print("You can now close this script and run your main bot.")
    
    await client.close()

client.run(BOT_TOKEN)