import asyncio
import logging

import pytz
from config import config

# A dictionary that remembers which guild belongs to which audiocontroller
guild_to_audiocontroller = {}

# A dictionary that remembers which settings belongs to which guild
guild_to_settings = {}

LOGGER = logging.getLogger(__name__)


def get_guild(bot, command):
    """
    Gets the guild a command belongs to.
    Useful, if the command was sent via pm.
    """
    if command.guild is not None:
        return command.guild
    for guild in bot.guilds:
        for channel in guild.voice_channels:
            if command.author in channel.members:
                return guild
    return None


async def connect_to_channel(guild, dest_channel_name, ctx, switch=False, default=True):
    """Connects the bot to the specified voice channel.

    Args:
        guild: The guild for witch the operation should be performed.
        switch: Determines if the bot should disconnect
            from his current channel to switch channels.
        default: Determines if the bot should default to the first channel,
            if the name was not found.
    """
    for channel in guild.voice_channels:
        if str(channel.name).strip() == str(dest_channel_name).strip():
            if switch:
                try:
                    await guild.voice_client.disconnect()
                except:
                    await ctx.send(config.NOT_CONNECTED_MESSAGE)

            await channel.connect()
            return

    if default:
        try:
            await guild.voice_channels[0].connect()
        except:
            await ctx.send(config.DEFAULT_CHANNEL_JOIN_FAILED)
    else:
        await ctx.send(config.CHANNEL_NOT_FOUND_MESSAGE + str(dest_channel_name))


async def is_connected(ctx):
    try:
        voice_channel = ctx.guild.voice_client.channel
        return voice_channel
    except:
        return None


async def play_check(ctx):

    sett = guild_to_settings[ctx.guild]

    cm_channel = sett.get("command_channel")
    vc_rule = sett.get("user_must_be_in_vc")

    if cm_channel is not None:
        if cm_channel != ctx.message.channel.id:
            await ctx.send(config.WRONG_CHANNEL_MESSAGE)
            return False

    if vc_rule is True:
        author_voice = ctx.message.author.voice
        bot_vc = ctx.guild.voice_client.channel
        if author_voice is None:
            await ctx.send(config.USER_NOT_IN_VC_MESSAGE)
            return False
        elif ctx.message.author.voice.channel != bot_vc:
            await ctx.send(config.USER_NOT_IN_VC_MESSAGE)
            return False


class Timer:
    def __init__(self, callback):
        self._callback = callback
        self._task = asyncio.create_task(self._job())

    async def _job(self):
        await asyncio.sleep(config.VC_TIMEOUT)
        await self._callback()

    def cancel(self):
        self._task.cancel()


class Tax:
    def __init__(self):
        self.nssf = 200
        self.personal_relief = 2400

    def nhif_calculator(self, salary) -> int:
        nhif = 0

        if salary <= 5999:
            nhif = 150
        elif salary >= 6000 and salary <= 7999:
            nhif = 300
        elif salary >= 8000 and salary <= 11999:
            nhif = 400
        elif salary >= 12000 and salary <= 14999:
            nhif = 500
        elif salary >= 15000 and salary <= 19999:
            nhif = 600
        elif salary >= 20000 and salary <= 24999:
            nhif = 750
        elif salary >= 25000 and salary <= 29999:
            nhif = 850
        elif salary >= 30000 and salary <= 34999:
            nhif = 900
        elif salary >= 35000 and salary <= 39999:
            nhif = 950
        elif salary >= 40000 and salary <= 44999:
            nhif = 1000
        elif salary >= 45000 and salary <= 49999:
            nhif = 1100
        elif salary >= 50000 and salary <= 59999:
            nhif = 1200
        elif salary >= 60000 and salary <= 69999:
            nhif = 1300
        elif salary >= 70000 and salary <= 79999:
            nhif = 1400
        elif salary >= 80000 and salary <= 89999:
            nhif = 1500
        elif salary >= 90000 and salary <= 99999:
            nhif = 1600
        elif salary >= 100000:
            nhif = 1700

        return nhif

    def calculate_tax(self, salary) -> float:

        taxable_pay = salary - self.nssf
        if salary > 0 and salary <= 24000:
            income_tax = taxable_pay * 0.1

        if salary > 24000 and salary <= 32333:
            first_iteration = taxable_pay - 24000
            first_tax = 2380
            second_tax = first_iteration * 0.25
            income_tax = first_tax + second_tax

        if salary > 32333:
            first_iteration = 8333
            second__iteration = taxable_pay - 24000 - 8333

            first_tax = 2380
            second_tax = 0.25 * first_iteration
            third_tax = 0.30 * second__iteration

            income_tax = first_tax + second_tax + third_tax

        return income_tax


def local_datetime(datetime_obj):
    utcdatetime = datetime_obj.replace(tzinfo=pytz.utc)
    tz = "Africa/Nairobi"
    return utcdatetime.astimezone(pytz.timezone(tz))
