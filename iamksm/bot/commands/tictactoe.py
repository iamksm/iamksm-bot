import random

import discord
from bot.utils import LOGGER
from discord.ext import commands

from iamksm.config import config


class Tictactoe(commands.Cog):
    def __init__(self, bot) -> None:
        super().__init__()
        self.bot = bot
        self.player1 = ""
        self.player2 = ""
        self.turn = ""
        self.gameOver = True
        self.board = []
        self.winning_conditions = [
            [0, 1, 2],
            [3, 4, 5],
            [6, 7, 8],
            [0, 3, 6],
            [1, 4, 7],
            [2, 5, 8],
            [0, 4, 8],
            [2, 4, 6],
        ]

    # Check Winner
    def check_winner(self, winning_conditions, mark):
        # global gameOver
        for condition in winning_conditions:
            if (
                self.board[condition[0]] == mark
                and self.board[condition[1]] == mark
                and self.board[condition[2]] == mark
            ):
                self.gameOver = True

    # TicTacToe Game
    @commands.command(
        name="tictactoe", description=config.HELP_TICTACTOE_LONG, help=config.HELP_TICTACTOE_SHORT
    )
    async def _tictactoe(self, ctx, p1: discord.Member, p2: discord.Member):
        if self.gameOver:
            self.board = [
                ":white_large_square:",
                ":white_large_square:",
                ":white_large_square:",
                ":white_large_square:",
                ":white_large_square:",
                ":white_large_square:",
                ":white_large_square:",
                ":white_large_square:",
                ":white_large_square:",
            ]
            self.turn = ""
            self.gameOver = False
            self.count = 0

            self.player1 = p1
            self.player2 = p2

            # print the board
            line = ""
            for x in range(len(self.board)):
                if x == 2 or x == 5 or x == 8:
                    line += " " + self.board[x]
                    await ctx.send(line)
                    line = ""
                else:
                    line += " " + self.board[x]

            # determine who goes first
            self.num = random.randint(1, 2)
            if self.num == 1:
                self.turn = self.player1
                await ctx.send("It is <@" + str(self.player1.id) + ">'s turn.")
            elif self.num == 2:
                self.turn = self.player2
                await ctx.send("It is <@" + str(self.player2.id) + ">'s turn.")
        else:
            await ctx.send("A game is already in progress! Finish it before starting a new one.")

    # placing No.s in the TicTacToe game
    @commands.command(
        name="place", description=config.HELP_PLACE_LONG, help=config.HELP_PLACE_SHORT
    )
    async def _place(self, ctx, pos: int):

        if not self.gameOver:
            mark = ""
            if self.turn == ctx.author:
                if self.turn == self.player1:
                    mark = ":regional_indicator_x:"
                elif self.turn == self.player2:
                    mark = ":o2:"
                if 0 < pos < 10 and self.board[pos - 1] == ":white_large_square:":
                    self.board[pos - 1] = mark
                    self.count += 1

                    # print the board
                    line = ""
                    for x in range(len(self.board)):
                        if x == 2 or x == 5 or x == 8:
                            line += " " + self.board[x]
                            await ctx.send(line)
                            line = ""
                        else:
                            line += " " + self.board[x]

                    self.check_winner(self.winning_conditions, mark)
                    LOGGER.info(self.count)
                    if self.gameOver:
                        await ctx.send(mark + " wins!")
                    elif self.count >= 9:
                        self.gameOver = True
                        await ctx.send("It's a tie!")

                    # switch turns
                    if self.turn == self.player1:
                        self.turn = self.player2
                    elif self.turn == self.player2:
                        self.turn = self.player1
                else:
                    await ctx.send(
                        "Be sure to choose an integer between 1 and 9 (inclusive) and an unmarked tile."  # noqa
                    )
            else:
                await ctx.send("It is not your turn.")
        else:
            await ctx.send("Please start a new game using the $tictactoe command.")

    # Error Handling
    @_tictactoe.error
    async def tictactoe_error(self, ctx, error):
        LOGGER.error(error)
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please mention 2 players for this command.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Please make sure to mention/ping players (ie. <@688534433879556134>).")

    @_place.error
    async def place_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please enter a position you would like to mark.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Please make sure to enter an integer.")


def setup(bot):
    bot.add_cog(Tictactoe(bot))
