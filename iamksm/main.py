import os

import discord
from bot.utils import LOGGER
from config import config
from discord.ext import commands

intents = discord.Intents.all()
intents.members = True
intents.typing = True
intents.presences = True
intents.reactions = True

initial_extensions = [
    "bot.commands.music",
    "bot.commands.general",
    "bot.commands.kra_calculator",
    "bot.commands.yts_scraper",
    "bot.commands.tictactoe",
    "bot.plugins.events",
]
client = commands.Bot(
    command_prefix=config.BOT_PREFIX,
    intents=intents,
    pm_help=True,
    case_insensitive=True,
)

if __name__ == "__main__":

    config.ABSOLUTE_PATH = os.path.dirname(os.path.abspath(__file__))
    config.COOKIE_PATH = config.ABSOLUTE_PATH + config.COOKIE_PATH

    if config.BOT_TOKEN == "":
        LOGGER.info("Error: No bot token!")
        exit

    for extension in initial_extensions:
        try:
            client.load_extension(extension)
        except Exception as e:
            LOGGER.error(e)

client.run(os.getenv("TOKEN"), bot=True, reconnect=True)
