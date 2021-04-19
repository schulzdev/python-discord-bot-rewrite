import json
import discord
from discord.ext import commands
import youtube_dl
from discord.voice_client import VoiceClient
import asyncio
import time

with open("./data.json") as file:
    token_file = json.load(file)

token = token_file["Token"]

bot = commands.Bot(command_prefix="!")



youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}


ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)



@bot.command()
async def kick(ctx, user: discord.Member, *, reason=""):
    await user.kick(reason=reason)
    await ctx.send(f"The user {user.mention} has been kicked!")

@bot.command()
async def play(ctx, url):
    if not ctx.message.author.voice:
        await ctx.send("You need to be connected to a voice channel to use the music bot!")
        return

    else:
        channel = ctx.message.author.voice.channel

    await channel.connect()

    server = ctx.message.guild
    voice_channel = server.voice_client

    async with ctx.typing():
        player = await YTDLSource.from_url(url, loop=bot.loop)
        voice_channel.play(player, after=lambda e: print("Error. %s" %e if e else None))

    e = discord.Embed(title="Now Playing:", description=f"[**{player.title}**]({url})", color=0xE6E6EA)
    await ctx.send(embed=e)

@bot.command()
async def stop(ctx):
    user_client = ctx.message.guild.voice_client
    await user_client.disconnect()
    
    
@bot.command()
async def delete(ctx, amount=5):
    roles = []
    for role in ctx.message.author.roles:
        roles.append(role.name)
        
    if "Admin" in roles:
        amount = int(amount) + 1
        await ctx.channel.purge(limit = amount)
        await ctx.send(f"{amount} Messages deleted.")
        time.sleep(1)
        await ctx.channel.purge(limit=1)
    else:
        await ctx.send(f"{ctx.message.author.mention} You do not have the rights to delete messages!")
        time.sleep(1)
        await ctx.channel.purge(limit=2)
    
    
    

bot.run(token)
