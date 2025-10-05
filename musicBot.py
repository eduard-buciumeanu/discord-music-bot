import os, discord, asyncio
from discord.ext import commands
from discord import app_commands
import yt_dlp
from dotenv import load_dotenv

load_dotenv()
intens = discord.Intents.default()
intens.message_content = True

FFMPEG_OPTIONS = {'options' : '-vn'}
YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': True}

class MusicBot(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.queue = []

    @commands.command()
    async def play(self, ctx, *, search):
        voice_channel = ctx.author.voice.channel if ctx.author.voice else None
        if not voice_channel:
            return await ctx.send(f"You're not in a voice channel!")
        if not ctx.voice_client:
            await voice_channel.connect()

        async with ctx.typing():

            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl: # type: ignore
                info = ydl.extract_info(f"ytsearch:{search}", download=False)
                if 'entries' in info:
                    info = info['entries'][0]
                
                url = info['url'] if 'url' in info else 'Unknown'
                title = info['title'] if 'title' in info else 'Unknown'

                self.queue.append((url, title))
                await ctx.send(f"Added to queue: **{title}**")
            
        if not ctx.voice_client.is_playing():
            await self.play_next(ctx)

    async def play_next(self, ctx):

        if self.queue:
            url, title = self.queue.pop(0)
            source = await discord.FFmpegOpusAudio.from_probe(url, **FFMPEG_OPTIONS)
            ctx.voice_client.play(source, after=lambda _:self.client.loop.create_task(self.play_next(ctx)))
            await ctx.send(f'Now playing **{title}**')
        elif not ctx.voice_client.is_playing():
            await ctx.send("queue is empty!")
        
    @commands.command()
    async def skip(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("Skipped")

    @commands.command()
    async def pause(self, ctx):
        """Pause / resume the current track."""
        vc = ctx.voice_client
        if not vc or not vc.is_connected():
            return await ctx.send("I'm not in a voice channel.")
        
        if vc.is_paused():          # already paused → resume
            vc.resume()
            await ctx.send("▶️ Resumed.")
        elif vc.is_playing():       # playing → pause
            vc.pause()
            await ctx.send("⏸️ Paused.")
        else:
            await ctx.send("Nothing is playing right now.")

    @commands.command()
    async def stop(self, ctx):
        """Stop playback, clear the queue and leave the channel."""
        vc = ctx.voice_client
        if not vc or not vc.is_connected():
            return await ctx.send("I'm not in a voice channel.")

        self.queue.clear()          # empty the queue
        vc.stop()                   # stop current track
        await vc.disconnect()
        await ctx.send("⏹️ Stopped and cleared the queue.")

client = commands.Bot(command_prefix="!", intents=intens)

async def main():
    await client.add_cog(MusicBot(client))
    await client.start(os.getenv("BOT_TOKEN")) # type: ignore

asyncio.run(main())
