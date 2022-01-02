import urllib

import discord
import requests
from bs4 import BeautifulSoup
from discord.ext import commands
from more_itertools import grouper

from iamksm.config import config


class YTS(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    async def scrapeSite(self, description, search_results_link, channel):
        search_results_html_page = requests.get(search_results_link).text
        search_results_soup = BeautifulSoup(search_results_html_page, "lxml")
        search_results_movies = search_results_soup.find_all(
            "div", class_="browse-movie-wrap col-xs-10 col-sm-4 col-md-5 col-lg-4"
        )

        for movies in grouper(search_results_movies, 10, None):
            embed = discord.Embed(
                title="RESULTS FROM YTS!",
                description=description,
                color=discord.Colour(0x2EB82E),
            )
            url = "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/Logo-YTS.svg/1920px-Logo-YTS.svg.png"  # noqa
            embed.set_thumbnail(url=url)
            for movie in movies:
                if movie is None:
                    break
                title = str(movie.find("a", class_="browse-movie-title").text).lower()
                year = movie.find("div", class_="browse-movie-year").text
                link = movie.find("a")["href"]
                image = movie.find("img", class_="img-responsive")["src"]
                rating = movie.find("h4", class_="rating").text
                categories = ", ".join([el.text for el in movie.select("h4:not(.rating)")])
                embed.add_field(
                    name=title.title() + f" | ({year}) | ({rating})",
                    value=link,
                    inline=False,
                )
                embed.add_field(name=categories, value="---" * 20)

                if len(search_results_movies) == 1:
                    embed.set_image(url=image)
        await channel.send(embed=embed)

    @commands.command(
        name="search", description=config.HELP_SEARCH_LONG, help=config.HELP_SEARCH_SHORT
    )
    async def _search(self, ctx, *args):
        local_args = locals()
        # make arg url safe
        arg = urllib.parse.quote(str(" ".join(local_args["args"])).lower())
        search_results_link = "https://yts.mx/browse-movies/" + arg + "/all/all/0/year/0/all"
        description = "Movie(s) you searched"
        channel = ctx.channel
        await self.scrapeSite(description, search_results_link, channel)

    @commands.command(
        name="featured", description=config.HELP_FEATURED_LONG, help=config.HELP_FEATURED_SHORT
    )
    async def _featured(self, ctx):
        url = "https://yts.mx/browse-movies/0/all/all/0/featured/0/all"
        description = "Featured Movies"
        channel = ctx.channel
        await self.scrapeSite(description, url, channel)


def setup(bot):
    bot.add_cog(YTS(bot))
