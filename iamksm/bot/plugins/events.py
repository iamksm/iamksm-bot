import asyncio
import datetime
import random

import discord
from babel import numbers
from bot import linkutils, utils
from bot.audiocontroller import AudioController
from bot.settings import Settings
from config import config
from discord.ext import commands

# Bot Statuses
activities = [
    (discord.ActivityType.playing, "with iamksm"),
    (discord.ActivityType.watching, "over {guilds} Servers"),
    (discord.ActivityType.watching, "over {members} Members"),
    (discord.ActivityType.listening, "{prefix} commands"),
]
timer = 10  # 10 seconds

# TODO: Create way to send message to user who made suggestion


class Events(commands.Cog, utils.Tax):
    def __init__(self, bot):
        self.bot = bot
        self.nssf = 200
        self.personal_relief = 2400
        self.empty_array = []
        self.dead_chat = [
            "dead chat",
            "ded chat",
            "chat dead",
            "dead server",
            "boring server",
        ]
        self.db = {}
        self.db["TO_BAN"] = []
        self.db["WATCHED"] = {}
        self.images = [
            "https://media1.tenor.com/images/f7ad58f17084a81fde2da96ddaa94edd/tenor.gif?itemid=18146171",  # noqa
            "https://media1.tenor.com/images/e2726f8433b913452d9a2f6768c49913/tenor.gif?itemid=4781301",  # noqa
            "https://media1.tenor.com/images/55b71cfa4bb363418b3833eaf1ee477d/tenor.gif?itemid=4941248",  # noqa
            "https://media1.tenor.com/images/939041d7709c44d052e4ddd1ca2f66a0/tenor.gif?itemid=13295259",  # noqa
            "https://media1.tenor.com/images/1f1378bacd3e8cd1c51bf829f4c08f4d/tenor.gif?itemid=22075897",  # noqa
            "https://media1.tenor.com/images/1771637ecbf5a19e226b951f3c133f42/tenor.gif?itemid=9304816",  # noqa
        ]

    @commands.Cog.listener()
    async def on_ready(self):
        print(config.STARTUP_MESSAGE)
        utils.LOGGER.info(config.STARTUP_MESSAGE)

        if not self.db.get("WATCHED"):
            self.db["WATCHED"] = {}

        if not self.db.get("TO_BAN"):
            self.db["TO_BAN"] = []

        for guild in self.bot.guilds:
            await self.register(guild)
            utils.LOGGER.info("Joined {}".format(guild.name))

            if not guild.public_updates_channel:
                await guild.system_channel.send("Please setup your public updates channel")
        print(config.STARTUP_COMPLETE_MESSAGE)
        utils.LOGGER.info(config.STARTUP_COMPLETE_MESSAGE)
        while True:
            guildCount = len(self.bot.guilds)
            memberCount = len(list(self.bot.get_all_members()))
            randomGame = random.choice(activities)
            await self.bot.change_presence(
                activity=discord.Activity(
                    type=randomGame[0],
                    name=randomGame[1].format(
                        guilds=guildCount, members=memberCount, prefix=config.BOT_PREFIX
                    ),
                )
            )
            self.db["WATCHED"] = {}
            await asyncio.sleep(timer)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        utils.LOGGER.info(guild.name)
        categories = guild.categories
        cat_exists = False
        for cat in categories:
            if "Massok" in cat.name:
                cat_exists = True

        if not cat_exists:
            try:
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    guild.me: discord.PermissionOverwrite(read_messages=True),
                }
                category = await guild.create_category(
                    name="Massok",
                    reason="The bot will use this section for system messages",
                    overwrites=overwrites,
                    position=0,
                )
                channel = await guild.create_text_channel(
                    name="Massok messages", overwrites=overwrites, category=category
                )
            except Exception as e:
                print(e)
        else:
            channels = await guild.fetch_channels()
            for chan in channels:
                if "Massok messages" in chan.name:
                    channel = chan

        await channel.send(
            "Run $set ban_role <ban role name> and $set default_role <default role name> to set ban role and the default server role for when a member joins"  # noqa
        )
        await self.register(guild)

    async def register(self, guild):

        utils.guild_to_settings[guild] = Settings(guild)
        utils.guild_to_audiocontroller[guild] = AudioController(self.bot, guild)

        sett = utils.guild_to_settings[guild]
        try:
            await guild.me.edit(nick=sett.get("default_nickname"))
        except:
            pass

        if config.GLOBAL_DISABLE_AUTOJOIN_VC is True:
            return

        vc_channels = guild.voice_channels

        if sett.get("vc_timeout") is False:
            if sett.get("start_voice_channel") is None:
                try:
                    await utils.guild_to_audiocontroller[guild].register_voice_channel(
                        guild.voice_channels[0]
                    )
                except Exception as e:
                    utils.LOGGER.error(e)

            else:
                for vc in vc_channels:
                    if vc.id == sett.get("start_voice_channel"):
                        try:
                            await utils.guild_to_audiocontroller[guild].register_voice_channel(
                                vc_channels[vc_channels.index(vc)]
                            )
                        except Exception as e:
                            utils.LOGGER.error(e)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild = member.guild
        sett = utils.guild_to_settings[guild]
        utils.guild_to_settings[guild] = Settings(guild)

        if guild.get_member(self.bot.user.id).permissions_in(guild.system_channel).send_messages:
            channel = guild.get_channel(guild.system_channel.id)
        else:
            channels = await guild.fetch_channels()
            for chan in channels:
                if "Massok messages" in chan.name:
                    channel = chan

        if channel:
            embed = discord.Embed(
                description=f"Welcome to **{member.guild.name}!**",
            )
            embed.set_thumbnail(url=member.avatar_url)
            embed.set_author(name=member.name, icon_url=member.avatar_url)
            embed.set_footer(text=member.guild, icon_url=member.guild.icon_url)
            embed.timestamp = utils.local_datetime(datetime.datetime.now())

            await channel.send(embed=embed)

        role = discord.utils.get(guild.roles, id=sett.config["default_role"])
        try:
            await member.add_roles(role)
        except discord.Forbidden:
            utils.LOGGER.error(f"Unable to assign the default role to {member.name}")

    @commands.Cog.listener()
    async def on_message(self, message):

        if message.author == self.bot.user:
            return

        bot = discord.ClientUser.bot
        if message.author is bot:
            return

        if str(message.channel.type).lower() == "private":
            if not str(message.content.split(" ")[0].lower()) == "tax":
                guilds = self.bot.guilds
                author_guilds = {}
                guild_names = []
                legit_guilds = []

                for guild in guilds:
                    if guild.public_updates_channel:
                        if (
                            guild.get_member(self.bot.user.id)
                            .permissions_in(guild.public_updates_channel)
                            .send_messages
                        ):
                            legit_guilds.append(guild)

                for guild in legit_guilds:
                    if message.author in guild.members:
                        author_guilds.update({guild.name.upper(): guild})
                        guild_names.append(guild.name.upper())

                if message.content not in guild_names:
                    if len(author_guilds.keys()) == 1:
                        guild = author_guilds[guild_names[0]]
                    else:
                        await message.channel.send(
                            "Please copy guild name you want to send the message to"
                        )

                        for name in guild_names:
                            await message.channel.send(name)

                        def check(m):
                            return m.content.upper() in guild_names and m.channel == message.channel

                        msg = await self.bot.wait_for("message", timeout=60, check=check)
                        guild = author_guilds[msg.content]
                        await message.channel.send("Chosen server is {.name}!".format(guild))
                elif message.content in guild_names:
                    return

                try:
                    modmail_channel = discord.utils.find(
                        lambda c: c.id == guild.public_updates_channel.id,
                        guild.channels,
                    )
                except Exception:
                    channels = await guild.fetch_channels()
                    for chan in channels:
                        if "Massok messages" in chan.name:
                            modmail_channel = chan

                if message.attachments != self.empty_array:
                    files = message.attachments
                    await modmail_channel.send("[" + message.author.mention + "]")
                    await message.channel.send(
                        f"Hello, {message.author.mention} The Mods will get back to you shortly"
                    )

                    for file in files:
                        await modmail_channel.send(file.url)

                else:
                    await modmail_channel.send(
                        "[" + message.author.mention + "] " + message.content
                    )
                    await message.channel.send(
                        f"Hello, {message.author.mention} The Mods will get back to you shortly"
                    )
            if str(message.content.split(" ")[0].lower()) == "tax":
                try:
                    salary = int(message.content.split(" ")[1])
                except ValueError:
                    embed = discord.Embed(
                        title="KRA TAX CALCULATOR",
                        description="I can only compute Integers",
                        color=discord.Color.red(),
                    )
                    embed.set_thumbnail(
                        url="https://pbs.twimg.com/profile_images/1412006848857772032/9txppbC0.jpg"
                    )
                    return await message.channel.send(embed=embed)

                if salary >= 0 and salary <= 23999:
                    embed = discord.Embed(
                        title="KRA TAX CALCULATOR",
                        description="P.A.Y.E is chargeable to persons of employment with monthly income of Kshs. 24,000 and above",  # noqa
                        color=discord.Color.red(),
                    )
                    embed.set_thumbnail(
                        url="https://pbs.twimg.com/profile_images/1412006848857772032/9txppbC0.jpg"
                    )
                    return await message.channel.send(embed=embed)

                taxable_pay = salary - self.nssf
                income_tax = self.calculate_tax(salary)
                nhif = self.nhif_calculator(salary)

                if salary >= 24000:
                    PAYE = income_tax - self.personal_relief
                else:
                    PAYE = 0

                pay_after_tax = taxable_pay - PAYE
                net_pay = pay_after_tax - nhif - 20

                format_currency = numbers.format_currency

                salary = format_currency(salary, "KES", locale="en_KE")
                NSSF = format_currency(self.nssf, "KES", locale="en_KE")
                taxable_pay = format_currency(taxable_pay, "KES", locale="en_KE")
                income_tax = format_currency(income_tax, "KES", locale="en_KE")
                nhif = format_currency(nhif, "KES", locale="en_KE")
                PAYE = format_currency(PAYE, "KES", locale="en_KE")
                pay_after_tax = format_currency(pay_after_tax, "KES", locale="en_KE")
                net_pay = format_currency(net_pay, "KES", locale="en_KE")
                personal_relief = format_currency(self.personal_relief, "KES", locale="en_KE")

                payslip = {
                    "BASIC PAY": salary,
                    "NSSF": NSSF,
                    "TAXABLE PAY": taxable_pay,
                    "INCOME TAX": income_tax,
                    "PERSONAL RELIEF": personal_relief,
                    "P.A.Y.E.": PAYE,
                    "PAY AFTER TAX": pay_after_tax,
                    "NHIF": nhif,
                    "NET PAY": net_pay,
                }

                utils.LOGGER.info(payslip)

                embed = discord.Embed(
                    title="KRA TAX CALCULATOR",
                    description="INCOME TAX",
                    color=discord.Color.red(),
                )
                embed.set_thumbnail(
                    url="https://pbs.twimg.com/profile_images/1412006848857772032/9txppbC0.jpg"
                )
                embed.add_field(name="BASIC PAY", value=salary.replace("Ksh", "Ksh ")),
                embed.add_field(name="NSSF", value=NSSF.replace("Ksh", "Ksh ")),
                embed.add_field(name="TAXABLE PAY", value=taxable_pay.replace("Ksh", "Ksh ")),
                embed.add_field(name="INCOME TAX", value=income_tax.replace("Ksh", "Ksh ")),
                embed.add_field(
                    name="PERSONAL RELIEF", value=personal_relief.replace("Ksh", "Ksh ")
                ),
                embed.add_field(name="P.A.Y.E.", value=PAYE.replace("Ksh", "Ksh ")),
                embed.add_field(name="PAY AFTER TAX", value=pay_after_tax.replace("Ksh", "Ksh ")),
                embed.add_field(name="NHIF", value=nhif.replace("Ksh", "Ksh ")),
                embed.add_field(
                    name="======================================",
                    value="=====================================",
                    inline=False,
                )
                embed.add_field(name="NET PAY", value=net_pay.replace("Ksh", "Ksh "), inline=False),

                await message.channel.send(embed=embed)
                return

        if str(message.channel.type).lower() != "private":
            if (
                message.channel == message.guild.public_updates_channel
                and message.content.startswith("<")
            ):
                member_object = message.mentions[0]

                if message.attachments != self.empty_array:
                    files = message.attachments

                    for file in files:
                        await member_object.send(file.url)
                else:
                    index = message.content.index(" ")
                    string = message.content
                    mod_message = string[index:]
                    await member_object.send(mod_message)
                    guild = message.guild

            else:
                guild = message.guild
                utils.guild_to_settings[guild] = Settings(guild)
                sett = utils.guild_to_settings[guild]
                ban_role = sett.get("ban_role")
                everyone = sett.get("everyone_role")
                role = discord.utils.get(guild.roles, id=ban_role)
                # Spamming protection
                if role:
                    try:
                        if message.author.top_role.id == ban_role:
                            await message.guild.ban(
                                message.author, reason="Spamming", delete_message_days=1
                            )
                            await modmail_channel.send(f"{message.author.mention} has been banned")
                            if message.author.name in self.db["TO_BAN"]:
                                self.db["TO_BAN"].remove(message.author.name)
                            return
                    except Exception as e:
                        utils.LOGGER.error(e)

                    banned_not_top_role = True
                    if message.author.name in self.db["WATCHED"].keys():
                        self.db["WATCHED"][message.author.name] += 1
                        if self.db["WATCHED"][message.author.name] > 5:
                            if message.author.name in self.db["TO_BAN"]:
                                await message.guild.ban(
                                    message.author,
                                    reason="Spamming",
                                    delete_message_days=1,
                                )
                                self.db["TO_BAN"].remove(message.author.name)
                            else:
                                # Give ban role
                                while banned_not_top_role:
                                    if message.author.top_role.id != everyone:
                                        await message.author.remove_roles(message.author.top_role)
                                    else:
                                        await message.author.add_roles(role)
                                        banned_not_top_role = False

                                if message.author.name not in self.db["TO_BAN"]:
                                    self.db["TO_BAN"].append(message.author.name)

                    else:
                        self.db["WATCHED"][message.author.name] = 1

                if message.guild:
                    sett = utils.guild_to_settings[message.guild]
                    button_name = sett.get("button_emote")

                    if button_name == "":
                        return

        host = linkutils.identify_url(message.content)

        guild = message.guild
        if guild:
            emoji = discord.utils.get(guild.emojis, name=button_name)

            if host == linkutils.Sites.YouTube:
                if emoji:
                    await message.add_reaction(emoji)

            if host == linkutils.Sites.Spotify:
                if emoji:
                    await message.add_reaction(emoji)

            if host == linkutils.Sites.Spotify_Playlist:
                if emoji:
                    await message.add_reaction(emoji)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, reaction):

        serv = self.bot.get_guild(reaction.guild_id)

        sett = utils.guild_to_settings[serv]
        button_name = sett.get("button_emote")

        if button_name == "":
            return

        if reaction.emoji.name == button_name:
            channels = serv.text_channels

            for chan in channels:
                if chan.id == reaction.channel_id:
                    if reaction.member == self.bot.user:
                        return

                    try:
                        if reaction.member.voice.channel is None:
                            return
                    except:
                        message = await chan.fetch_message(reaction.message_id)
                        await message.remove_reaction(reaction.emoji, reaction.member)
                        return
                    message = await chan.fetch_message(reaction.message_id)
                    await message.remove_reaction(reaction.emoji, reaction.member)

            current_guild = utils.get_guild(self.bot, message)
            audiocontroller = utils.guild_to_audiocontroller[current_guild]

            url = linkutils.get_url(message.content)

            host = linkutils.identify_url(url)

            if host == linkutils.Sites.Spotify:
                await audiocontroller.process_song(url)

            if host == linkutils.Sites.Spotify.Spotify_Playlist:
                await audiocontroller.process_song(url)

            if host == linkutils.Sites.YouTube:
                await audiocontroller.process_song(url)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        # Ignore these errors
        ignored = (commands.CommandNotFound, commands.UserInputError)
        if isinstance(error, ignored):
            return

        if isinstance(error, commands.CommandOnCooldown):
            # If the command is currently on cooldown trip this
            m, s = divmod(error.retry_after, 60)
            h, m = divmod(m, 60)
            if int(h) == 0 and int(m) == 0:
                await ctx.send(f" You must wait {int(s)} seconds to use this command!")
            elif int(h) == 0 and int(m) != 0:
                await ctx.send(
                    f" You must wait {int(m)} minutes and {int(s)} seconds to use this command!"
                )
            else:
                await ctx.send(
                    f" You must wait {int(h)} hours, {int(m)} minutes and {int(s)} seconds to use this command!"  # noqa
                )
        elif isinstance(error, commands.CheckFailure):
            # If the command has failed a check, trip this
            await ctx.send("Hey! You lack permission to use this command.")

        elif isinstance(error, commands.CommandError):
            await ctx.send(error)

        raise error


def setup(bot):
    bot.add_cog(Events(bot))
