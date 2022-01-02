import datetime
import platform
import time
from collections import Counter

import discord
import pytz
from bot import utils
from bot.audiocontroller import AudioController
from bot.utils import guild_to_audiocontroller, guild_to_settings
from config import config
from discord.ext import commands
from discord.ext.commands import has_permissions


class General(commands.Cog):
    """A collection of the commands for moving the bot around in you server.

    Attributes:
        bot: The instance of the bot that is executing the commands.
    """

    def __init__(self, bot):
        self.bot = bot
        self.starttime = datetime.datetime.now()

    def local_datetime(self, datetime_obj):
        utcdatetime = datetime_obj.replace(tzinfo=pytz.utc)
        tz = "Africa/Nairobi"
        return utcdatetime.astimezone(pytz.timezone(tz))

    # logic is split to uconnect() for wide usage
    @commands.command(
        name="connect",
        description=config.HELP_CONNECT_LONG,
        help=config.HELP_CONNECT_SHORT,
        aliases=["c"],
    )
    async def _connect(self, ctx):  # dest_channel_name: str
        current_guild = utils.get_guild(self.bot, ctx.message)
        audiocontroller = utils.guild_to_audiocontroller[current_guild]
        await audiocontroller.uconnect(ctx)

    @commands.command(
        name="disconnect",
        description=config.HELP_DISCONNECT_LONG,
        help=config.HELP_DISCONNECT_SHORT,
        aliases=["dc"],
    )
    async def _disconnect(self, ctx, guild=False):
        current_guild = utils.get_guild(self.bot, ctx.message)
        audiocontroller = utils.guild_to_audiocontroller[current_guild]
        await audiocontroller.udisconnect()

    @commands.command(
        name="reset",
        description=config.HELP_DISCONNECT_LONG,
        help=config.HELP_DISCONNECT_SHORT,
        aliases=["rs", "restart"],
    )
    async def _reset(self, ctx):
        current_guild = utils.get_guild(self.bot, ctx.message)

        if current_guild is None:
            await ctx.send(config.NO_GUILD_MESSAGE)
            return
        await utils.guild_to_audiocontroller[current_guild].stop_player()
        await current_guild.voice_client.disconnect(force=True)

        guild_to_audiocontroller[current_guild] = AudioController(self.bot, current_guild)
        await guild_to_audiocontroller[current_guild].register_voice_channel(
            ctx.author.voice.channel
        )

        await ctx.send(
            "{} Connected to {}".format(":white_check_mark:", ctx.author.voice.channel.name)
        )

    @commands.command(
        name="changechannel",
        description=config.HELP_CHANGECHANNEL_LONG,
        help=config.HELP_CHANGECHANNEL_SHORT,
        aliases=["cc"],
    )
    async def _change_channel(self, ctx):
        current_guild = utils.get_guild(self.bot, ctx.message)

        vchannel = await utils.is_connected(ctx)
        if vchannel == ctx.author.voice.channel:
            await ctx.send("{} Already connected to {}".format(":white_check_mark:", vchannel.name))
            return

        if current_guild is None:
            await ctx.send(config.NO_GUILD_MESSAGE)
            return
        await utils.guild_to_audiocontroller[current_guild].stop_player()
        await current_guild.voice_client.disconnect(force=True)

        guild_to_audiocontroller[current_guild] = AudioController(self.bot, current_guild)
        await guild_to_audiocontroller[current_guild].register_voice_channel(
            ctx.author.voice.channel
        )

        await ctx.send(
            "{} Switched to {}".format(":white_check_mark:", ctx.author.voice.channel.name)
        )

    @commands.command(name="ping", description=config.HELP_PING_LONG, help=config.HELP_PING_SHORT)
    async def _ping(self, ctx):
        ping = ctx.message
        pong = await ctx.send("**:ping_pong:** Pong!")
        delta = pong.created_at - ping.created_at
        delta = int(delta.total_seconds() * 1000)
        await pong.edit(
            content=f":ping_pong: Pong! ({delta} ms)\n*Discord WebSocket latency: {round(self.bot.latency, 5)} ms*"  # noqa
        )
        time.sleep(1)

    @commands.command(
        name="setting",
        description=config.HELP_SHUFFLE_LONG,
        help=config.HELP_SETTINGS_SHORT,
        aliases=["settings", "set"],
    )
    @has_permissions(administrator=True)
    async def _settings(self, ctx, *args):

        sett = guild_to_settings[ctx.guild]

        if len(args) == 0:
            await ctx.send(embed=await sett.format())
            return

        args_list = list(args)
        args_list.remove(args[0])

        response = await sett.write(args[0], " ".join(args_list), ctx)

        if response is None:
            await ctx.send("`Error: Setting not found`")
        elif response is True:
            await ctx.send("Setting updated!")

    @commands.command(
        name="addbot",
        description=config.HELP_ADDBOT_LONG,
        help=config.HELP_ADDBOT_SHORT,
    )
    async def _addbot(self, ctx):
        embed = discord.Embed(
            title="Invite",
            description=config.ADD_MESSAGE
            + f"(https://discordapp.com/oauth2/authorize?client_id={self.bot.user.id}&permissions=1394089389781&scope=applications.commands%20bot>)",  # noqa
        )

        await ctx.send(embed=embed)

    @commands.command(
        name="purge", description=config.HELP_PURGE_LONG, help=config.HELP_PURGE_SHORT
    )
    @commands.has_permissions(manage_messages=True)
    async def _purge(self, ctx, amount=10):
        await ctx.channel.purge(limit=amount)

    @commands.command(
        name="whois", description=config.HELP_WHO_IS_LONG, help=config.HELP_WHOIS_SHORT
    )
    async def _whois(self, ctx, member: discord.Member):
        embed = discord.Embed(
            title=member.name, description=member.mention, color=discord.Color.red()
        )
        embed.add_field(
            name="Name and Tag",
            value="{}#{}".format(member.name, member.discriminator),
            inline=True,
        )
        embed.add_field(name="User ID", value=member.id, inline=True)
        embed.add_field(
            name="Account Creation Date",
            value=self.local_datetime(member.created_at).strftime("%A, %B %d %Y @ %H:%M:%S %p %Z"),
            inline=False,
        )
        embed.add_field(
            name="Joined Server On",
            value=self.local_datetime(member.joined_at).strftime("%A, %B %d %Y @ %H:%M:%S %p %Z"),
            inline=False,
        )

        all_activities = []
        spotify = None
        for activity in member.activities:
            activity_name = activity.name
            if "spotify" in activity_name.lower():
                spotify = activity
            all_activities.append(activity_name)
        activities = "\n".join(all_activities) if all_activities else None
        embed.add_field(name="Activities", value=activities, inline=True)

        if spotify:
            embed.add_field(
                name="Spotify", value=f"{spotify.artist} - {spotify.title}", inline=True
            )

        roles = sorted([role for role in member.roles], reverse=True)
        mentions = [str(role.mention) for role in roles]
        del roles
        embed.add_field(name="Top Role", value=member.top_role, inline=False)
        embed.add_field(name="Roles", value=" , ".join(mentions), inline=False)

        embed.set_thumbnail(url=member.avatar_url)
        embed.set_footer(icon_url=ctx.author.avatar_url, text=f"Requested by {ctx.author.name}")

        await ctx.send(embed=embed)

    # Server info.

    @commands.command(
        name="server", description=config.HELP_SERVER_LONG, help=config.HELP_SERVER_SHORT
    )
    async def _server(self, ctx):
        name = str(ctx.guild.name)
        description = str(ctx.guild.description)

        owner = str(ctx.guild.owner)
        id = str(ctx.guild.id)
        region = str(ctx.guild.region)
        member_count = str(ctx.guild.member_count)

        icon = str(ctx.guild.icon_url)

        embed = discord.Embed(
            title=name + " Server Info",
            description=description,
            color=discord.Color.red(),
        )
        embed.set_thumbnail(url=icon)
        embed.add_field(name="Owner", value=owner, inline=True)
        embed.add_field(name="Server ID", value=id, inline=True)
        embed.add_field(name="Region", value=region, inline=False)
        embed.add_field(name="Member Count", value=member_count, inline=True)

        if ctx.guild.premium_subscribers:
            names = ctx.guild.premium_subscribers
            mentions = [str(name.mention) for name in names]
            del names
            embed.add_field(name="Current Server Boosters", value="\n".join(mentions), inline=False)
        embed.add_field(
            name="Server Creation Date",
            value=self.local_datetime(ctx.guild.created_at).strftime(
                "%A, %B %d %Y @ %H:%M:%S %p %Z"
            ),
            inline=False,
        )

        if ctx.guild.system_channel:
            embed.add_field(
                name="Standard Channel",
                value=f"#{ctx.guild.system_channel}",
                inline=True,
            )
            embed.add_field(
                name="AFK Voice Timeout",
                value=f"{int(ctx.guild.afk_timeout / 60)} min",
                inline=True,
            )
            embed.add_field(name="Guild Shard", value=ctx.guild.shard_id, inline=True)
        embed.set_footer(text="Bot by iamksm")
        await ctx.send(embed=embed)

    def get_uptime(self, days, hours, minutes, seconds):
        seconds = int(seconds)
        minutes = int(minutes)
        hours = int(hours)
        days = int(days)

        min_stat = "Minutes" if int(minutes) > 1 else "Minute"
        sec_stat = "Seconds" if seconds > 1 else "Second"
        hour_stat = "Hours" if hours > 1 else "Hour"
        day_stat = "Days" if days > 1 else "Day"

        if int(seconds) > 0:
            uptime = f"{seconds} {sec_stat}"

        if int(minutes) > 0:
            uptime = f"{minutes} {min_stat} and {seconds} {sec_stat}"

        if int(hours) > 0:
            uptime = f"{hours} {hour_stat}, {minutes} {min_stat} and {seconds} {sec_stat}"

        if int(days) > 0:
            uptime = f"{days} {day_stat}, {hours} {hour_stat}, {minutes} {min_stat} and {seconds} {sec_stat}"  # noqa

        return uptime

    @commands.command(name="stats", description=config.HELP_STATS_LONG, help=config.HELP_STATS_LONG)
    async def _stats(self, ctx):
        """
        A usefull command that displays bot statistics.
        """
        pythonVersion = platform.python_version()
        dpyVersion = discord.__version__
        serverCount = len(self.bot.guilds)
        memberCount = len(set(self.bot.get_all_members()))

        uptime = datetime.datetime.now() - self.starttime
        days = ((uptime.seconds / 3600) / 24) % 24
        hours = uptime.seconds / 3600
        minutes = (uptime.seconds / 60) % 60
        seconds = uptime.seconds % 60

        embed = discord.Embed(
            title=f"{self.bot.user.name} Stats",
            description="",
            colour=ctx.author.colour,
            timestamp=ctx.message.created_at,
        )

        embed.add_field(name="Bot Version:", value=config.BOT_VERSION)
        embed.add_field(name="Python Version:", value=pythonVersion)
        embed.add_field(name="Discord.Py Version", value=dpyVersion)
        embed.add_field(name="Total Guilds:", value=serverCount)
        embed.add_field(name="Total Users:", value=memberCount)
        embed.add_field(name="Uptime", value=self.get_uptime(days, hours, minutes, seconds))
        embed.add_field(name="Bot Developer:", value="<@459338191892250625>")

        embed.set_footer(text=f"Say hello to my little friend | {self.bot.user.name}")
        embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar_url)

        await ctx.send(embed=embed)

    @commands.command(
        name="games",
        aliases=["activities"],
        description=config.HELP_GAMES_LONG,
        help=config.HELP_GAMES_SHORT,
    )
    async def _games(self, ctx, *scope):
        """Shows which games are currently being played on the server"""
        games = Counter()
        for member in ctx.guild.members:
            for activity in member.activities:
                if not member.bot:
                    if isinstance(activity, discord.Game):
                        games[str(activity)] += 1
                    elif isinstance(activity, discord.Activity):
                        games[activity.name] += 1
        msg = ":chart: Games currently being played on this server\n"
        msg += "```js\n"
        msg += "{!s:40s}: {!s:>3s}\n".format("Name", "Number")
        chart = sorted(games.items(), key=lambda t: t[1], reverse=True)
        for index, (name, amount) in enumerate(chart):
            if len(msg) < 1950:
                msg += "{!s:40s}: {!s:>3s}\n".format(name, amount)
            else:
                amount = len(chart) - index
                msg += f"+ {amount} Others"
                break
        msg += "```"
        await ctx.send(msg)

    @commands.command(
        name="suggest", description=config.HELP_SUGGEST_LONG, help=config.HELP_SUGGEST_SHORT
    )
    async def _suggest(self, ctx, message):
        embed = discord.Embed(
            title=ctx.guild.name, description="Suggestion", color=ctx.author.color
        )
        embed.set_thumbnail(url=str(ctx.guild.icon_url))
        embed.add_field(name=ctx.author, value=message)
        owner = self.bot.get_user(459338191892250625)
        owner_dm = await owner.create_dm()
        await owner_dm.send(embed=embed)


def setup(bot):
    bot.add_cog(General(bot))
