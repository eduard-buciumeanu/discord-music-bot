import os, discord, asyncio
from discord.ext import commands
from discord import app_commands
import yt_dlp
from dotenv import load_dotenv

load_dotenv()
intens = discord.Intents.default()
intens.message_content = True

FFMPEG_OPTIONS = {'options': '-vn'}
YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': True}

class MusicBot(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.queue = []
        self.play_channel = None # Store the channel to send "Now playing" messages

    @app_commands.command(name="play", description="Play a song from YouTube")
    @app_commands.describe(search="The song or video to search for on YouTube")
    async def play(self, interaction: discord.Interaction, search: str):
        voice_channel = interaction.user.voice.channel if interaction.user.voice else None
        if not voice_channel:
            return await interaction.response.send_message(f"You're not in a voice channel!", ephemeral=True)
        
        await interaction.response.defer()
        
        # Set the channel for future "Now playing" messages
        self.play_channel = interaction.channel

        if not interaction.guild.voice_client:
            await voice_channel.connect()

        try:
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(f"ytsearch:{search}", download=False)
                if 'entries' in info:
                    info = info['entries'][0]
                
                url = info['url']
                title = info['title']

                self.queue.append((url, title))
                await interaction.followup.send(f"Added to queue: **{title}**")
            
            if not interaction.guild.voice_client.is_playing():
                await self.play_next()
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {e}")

    async def play_next(self):
        # Use the stored channel instead of the interaction object
        if self.play_channel is None:
            return # Don't do anything if we don't have a channel

        if self.queue:
            url, title = self.queue.pop(0)
            try:
                source = await discord.FFmpegOpusAudio.from_probe(url, **FFMPEG_OPTIONS)
                vc = self.play_channel.guild.voice_client
                # The after callback no longer needs the interaction
                vc.play(source, after=lambda e: self.client.loop.create_task(self.play_next()) if e is None else print(f"Player error: {e}"))
                await self.play_channel.send(f'Now playing **{title}**')
            except Exception as e:
                print(f"Error playing next song: {e}")
                await self.play_channel.send(f"Could not play the next song: **{title}**")
                # Try to play the next song in the queue
                await self.play_next()
        elif not self.play_channel.guild.voice_client.is_playing():
            await self.play_channel.send("Queue is empty!")

    @app_commands.command(name="skip", description="Skip the currently playing song")
    async def skip(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc and vc.is_playing():
            vc.stop()
            await interaction.response.send_message("Skipped")
        else:
            await interaction.response.send_message("Nothing is playing right now.", ephemeral=True)

    @app_commands.command(name="pause", description="Pause or resume the current track")
    async def pause(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if not vc or not vc.is_connected():
            return await interaction.response.send_message("I'm not in a voice channel.", ephemeral=True)
        
        if vc.is_paused():
            vc.resume()
            await interaction.response.send_message("▶️ Resumed.")
        elif vc.is_playing():
            vc.pause()
            await interaction.response.send_message("⏸️ Paused.")
        else:
            await interaction.response.send_message("Nothing is playing right now.", ephemeral=True)

    @app_commands.command(name="stop", description="Stop playback, clear the queue and leave the channel")
    async def stop(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if not vc or not vc.is_connected():
            return await interaction.response.send_message("I'm not in a voice channel.", ephemeral=True)

        self.queue.clear()
        self.play_channel = None # Clear the channel when stopping
        vc.stop()
        await vc.disconnect()
        await interaction.response.send_message("⏹️ Stopped and cleared the queue.")

# Use commands.Bot to get access to the 'tree'
client = commands.Bot(command_prefix="!", intents=intens)

@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')
    
    # Sync commands to a specific guild for instant updates.
    # This is highly recommended for development.
    # Replace YOUR_GUILD_ID with your actual server ID.
    # To get your server ID, right-click your server icon in Discord and click "Copy Server ID".
    # You may need to enable Developer Mode in your Discord settings (User Settings > Advanced > Developer Mode).
    GUILD_ID = os.getenv("GUILD_ID") # Recommended: Store guild ID in .env
    if GUILD_ID:
        guild_object = discord.Object(id=int(GUILD_ID))
        await client.tree.sync(guild=guild_object)
        print(f"Synced commands to guild {GUILD_ID}")
    else:
        # If no GUILD_ID is set, sync globally (can take up to an hour).
        await client.tree.sync()
        print("Synced commands globally. This may take up to an hour to update.")
    
    print('Bot is ready.')

async def main():
    await client.add_cog(MusicBot(client))
    await client.start(os.getenv("BOT_TOKEN"))

asyncio.run(main())