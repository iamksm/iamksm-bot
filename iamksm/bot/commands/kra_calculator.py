import babel.numbers
import discord
from bot.utils import LOGGER, Tax
from discord.ext import commands

from iamksm.config import config


class KraTaxCalculator(commands.Cog, Tax):
    """
    ==========
    INCOME TAX
    ==========
    On the first 24,000	10%
    On the next 8,333	25%
    On all income over 32,333	30%

    ============
    NHIF CHARGES
    ============
    Ksh. 0 to Ksh. 5,999 – Ksh. 150
    Ksh. 6,000 to Ksh. 7,999 – Ksh. 300
    Ksh. 8,000 to Ksh. 11,999 – Ksh. 400
    Ksh. 12,000 to Ksh. 14,999 – Ksh. 500
    Ksh. 15,000 to Ksh. 19,999 – Ksh. 600
    Ksh. 20,000 to Ksh. 24,999 – Ksh. 750
    Ksh. 25,000 to Ksh. 29,999 – Ksh. 850
    Ksh. 30,000 to Ksh. 34,999 – Ksh. 900
    Ksh. 35,000 to Ksh. 39,000 – Ksh. 950
    Ksh. 40,000 to Ksh. 44,999 – Ksh. 1,000
    Ksh. 45,000 to Ksh. 49,000 – Ksh. 1,100
    Ksh. 50,000 to Ksh. 59,999 – Ksh. 1,200
    Ksh. 60,000 to Ksh. 69,999 – Ksh. 1,300
    Ksh. 70,000 to Ksh. 79,999 – Ksh. 1,400
    Ksh. 80,000 to Ksh. 89,999 – Ksh. 1,500
    Ksh. 90,000 to Ksh. 99,999 – Ksh. 1,60
    Ksh. 100,000 and above – Ksh. 1,700
    """

    def __init__(self, bot):
        self.bot = bot
        self.nssf = 200
        self.personal_relief = 2400

    @commands.command(name="tax", description=config.HELP_TAX_LONG, help=config.HELP_TAX_SHORT)
    async def calculate_net_pay(self, ctx, salary):

        salary = int(salary)
        if salary >= 0 and salary <= 23999:
            embed = discord.Embed(
                title="KRA TAX CALCULATOR",
                description="P.A.Y.E is chargeable to persons of employment with monthly income of Kshs. 24,000 and above",  # noqa
                color=discord.Color.red(),
            )
            embed.set_thumbnail(
                url="https://pbs.twimg.com/profile_images/1412006848857772032/9txppbC0.jpg"
            )

            return await ctx.send(embed=embed)

        taxable_pay = salary - self.nssf
        income_tax = self.calculate_tax(salary)
        nhif = self.nhif_calculator(salary)

        if salary >= 24000:
            PAYE = income_tax - self.personal_relief
        else:
            PAYE = 0

        pay_after_tax = taxable_pay - PAYE
        net_pay = pay_after_tax - nhif - 20

        format_currency = babel.numbers.format_currency

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

        LOGGER.info(payslip)

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
        embed.add_field(name="PERSONAL RELIEF", value=personal_relief.replace("Ksh", "Ksh ")),
        embed.add_field(name="P.A.Y.E.", value=PAYE.replace("Ksh", "Ksh ")),
        embed.add_field(name="PAY AFTER TAX", value=pay_after_tax.replace("Ksh", "Ksh ")),
        embed.add_field(name="NHIF", value=nhif.replace("Ksh", "Ksh ")),
        embed.add_field(
            name="======================================",
            value="=====================================",
            inline=False,
        )
        embed.add_field(name="NET PAY", value=net_pay.replace("Ksh", "Ksh "), inline=False),

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(KraTaxCalculator(bot))
