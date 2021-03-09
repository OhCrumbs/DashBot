import asyncio
import discord
import random
import calendar

from typing import Any, Union
from discord.utils import get
from datetime import datetime

from redbot.core import Config, checks, commands, bank
from redbot.core.utils.chat_formatting import pagify, box
from redbot.core.utils.predicates import MessagePredicate
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS

from redbot.core.bot import Red

_MAX_BALANCE = 2 ** 63 - 1


class Coin(commands.Cog):
    """
    Collect Coins.
    """

    __author__ = "saurichable"
    __version__ = "1.1.4"

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=16548964843212314, force_registration=True
        )
        self.config.register_guild(
            amount=1,
            minimum=0,
            maximum=0,
            cooldown=86400,
            stealing=False,
            stealcd=43200,
            rate=0.5,
        )
        self.config.register_member(coins=0, next_coin=0, next_steal=0)
        self.config.register_role(coins=0, multiplier=1)

    @commands.command()
    @commands.guild_only()
    async def coin(self, ctx: commands.Context):
        """Get your daily dose of coins."""
        amount = int(await self.config.guild(ctx.guild).amount())
        coins = int(await self.config.member(ctx.author).coins())
        cur_time = calendar.timegm(ctx.message.created_at.utctimetuple())
        next_coin = await self.config.member(ctx.author).next_coin()
        if cur_time >= next_coin:
            if amount != 0:
                multipliers = []
                for role in ctx.author.roles:
                    role_multiplier = await self.config.role(role).multiplier()
                    if not role_multiplier:
                        role_multiplier = 1
                    multipliers.append(role_multiplier)
                coins += (amount * max(multipliers)) 
            else:
                minimum = int(await self.config.guild(ctx.guild).minimum())
                maximum = int(await self.config.guild(ctx.guild).maximum())
                amount = int(random.choice(list(range(minimum, maximum))))
                coins += amount
            if self._max_balance_check(coins):
                return await ctx.send(
                    "Uh oh, you have reached the maximum amount of coins that you can put in your bag. :frowning:"
                )
            next_coin = cur_time + await self.config.guild(ctx.guild).cooldown()
            await self.config.member(ctx.author).next_coin.set(next_coin)
            await self.config.member(ctx.author).coins.set(coins)
            await ctx.send(f"Here is your {amount} :cookie:")
        else:
            dtime = self.display_time(next_coin - cur_time)
            await ctx.send(f"Uh oh, you have to wait {dtime}.")

    @commands.command()
    @commands.guild_only()
    async def steal(self, ctx: commands.Context, target: discord.Member = None):
        """Steal coins from members."""
        cur_time = calendar.timegm(ctx.message.created_at.utctimetuple())
        next_steal = await self.config.member(ctx.author).next_steal()
        enabled = await self.config.guild(ctx.guild).stealing()
        author_coins = int(await self.config.member(ctx.author).coins())

        if not enabled:
            return await ctx.send("Uh oh, stealing is disabled.")
        if cur_time < next_steal:
            dtime = self.display_time(next_steal - cur_time)
            return await ctx.send(f"Uh oh, you have to wait {dtime}.")

        if not target:
            ids = await self._get_ids(ctx)
            while not target:
                target_id = random.choice(ids)
                target = ctx.guild.get_member(target_id)
        if target.id == ctx.author.id:
            return await ctx.send("Don't be silly, you can't steal from yourself.")
        target_coins = int(await self.config.member(target).coins())
        if target_coins == 0:
            return await ctx.send(
                f"Uh oh, {target.display_name} doesn't have any :cookie:"
            )

        await self.config.member(ctx.author).next_steal.set(cur_time + await self.config.guild(ctx.guild).stealcd())

        success_chance = random.randint(1, 100)
        if success_chance > 90:
            coins_stolen = int(target_coins * 0.5)
            if coins_stolen == 0:
                coins_stolen = 1
            stolen = random.randint(1, coins_stolen)
            author_coins += stolen
            if self._max_balance_check(author_coins):
                return await ctx.send(
                    "Uh oh, you have reached the maximum amount of coins that you can put in your bag. :frowning:\n"
                    f"You stole any coin of {target.display_name}."
                )
            target_coins -= stolen
            await ctx.send(f"You stole {stolen} :cookie: from {target.display_name}!")
        else:
            coins_penalty = int(author_coins * 0.25)
            if coins_penalty == 0:
                coins_penalty = 1
            if coins_penalty > 0:
                penalty = random.randint(1, coins_penalty)
                if author_coins < penalty:
                    penalty = author_coins
                if self._max_balance_check(target_coins + penalty):
                    return await ctx.send(
                        f"Uh oh, you got caught while trying to steal {target.display_name}'s :cookie:\n"
                        f"{target.display_name} has reached the maximum amount of coins, "
                        "so you haven't lost any."
                    )
                author_coins -= penalty
                target_coins += penalty
                await ctx.send(
                    f"You got caught while trying to steal {target.display_name}'s :cookie:\nYour penalty is {penalty} :cookie: which they got!"
                )
            else:
                return await ctx.send(
                    f"Uh oh, you got caught while trying to steal {target.display_name}'s :cookie:\n"
                    f"You don't have any coins, so you haven't lost any."
                )
        await self.config.member(target).coins.set(target_coins)
        await self.config.member(ctx.author).coins.set(author_coins)

    @commands.command()
    @commands.guild_only()
    async def gift(self, ctx: commands.Context, target: discord.Member, amount: int):
        """Gift someone some coins."""
        author_coins = int(await self.config.member(ctx.author).coins())
        if amount <= 0:
            return await ctx.send("Uh oh, amount has to be more than 0.")
        if target.id == ctx.author.id:
            return await ctx.send("Why would you do that?")
        if amount > author_coins:
            return await ctx.send("You don't have enough coins yourself!")
        target_coins = int(await self.config.member(target).coins())
        target_coins += amount
        if self._max_balance_check(target_coins):
            return await ctx.send(
                f"Uh oh, {target.display_name} has reached the maximum amount of coins that they can have in their bag. :frowning:"
            )
        author_coins -= amount
        await self.config.member(ctx.author).coins.set(author_coins)
        await self.config.member(target).coins.set(target_coins)
        await ctx.send(
            f"{ctx.author.mention} has gifted {amount} :cookie: to {target.mention}"
        )

    @commands.command(aliases=["jar"])
    @commands.guild_only()
    async def coin(self, ctx: commands.Context, target: discord.Member = None):
        """Check how many coins you have."""
        if not target:
            coins = int(await self.config.member(ctx.author).coins())
            await ctx.send(f"You have {coins} :cookie:")
        else:
            coins = int(await self.config.member(target).coins())
            await ctx.send(f"{target.display_name} has {coins} :cookie:")

    @commands.command()
    @commands.guild_only()
    async def coinexchange(self, ctx: commands.Context, amount: int):
        """Exchange coins."""
        if amount <= 0:
            return await ctx.send("Uh oh, amount has to be more than 0.")

        if not await bank.can_spend(ctx.author, amount):
            return await ctx.send(f"Uh oh, you cannot afford this.")
        await bank.withdraw_credits(ctx.author, amount)

        rate = await self.config.guild(ctx.guild).rate()
        new_coins = amount * rate

        coins = await self.config.member(ctx.author).coin()
        coins += new_coins
        await self.config.member(ctx.author).coin.set(coins)
        currency = await bank.get_currency_name(ctx.guild)
        await ctx.send(f"You have exchanged {amount} {currency} and got {new_coins} :cookie:\nYou now have {coins} :cookie:")

    @commands.command(aliases=["coinleaderboard"])
    @commands.guild_only()
    async def coinlb(self, ctx: commands.Context):
        """Display the server's coins leaderboard."""
        ids = await self._get_ids(ctx)
        lst = []
        pos = 1
        pound_len = len(str(len(ids)))
        header = "{pound:{pound_len}}{score:{bar_len}}{name:2}\n".format(
            pound="#",
            name="Name",
            score="Coins",
            pound_len=pound_len + 3,
            bar_len=pound_len + 9,
        )
        temp_msg = header
        for a_id in ids:
            a = get(ctx.guild.members, id=int(a_id))
            if not a:
                continue
            name = a.display_name
            coins = await self.config.member(a).coins()
            if coins == 0:
                continue
            score = "Coins"
            if a_id != ctx.author.id:
                temp_msg += (
                    f"{f'{pos}.': <{pound_len+2}} {coins: <{pound_len+8}} {name}\n"
                )
            else:
                temp_msg += (
                    f"{f'{pos}.': <{pound_len+2}} "
                    f"{coins: <{pound_len+8}} "
                    f"<<{name}>>\n"
                )
            if pos % 10 == 0:
                lst.append(box(temp_msg, lang="md"))
                temp_msg = header
            pos += 1
        if temp_msg != header:
            lst.append(box(temp_msg, lang="md"))
        if lst:
            if len(lst) > 1:
                await menu(ctx, lst, DEFAULT_CONTROLS)
            else:
                await ctx.send(lst[0])
        else:
            empty = "Nothing to see here."
            await ctx.send(box(empty, lang="md"))

    @commands.group(autohelp=True)
    @checks.admin_or_permissions(manage_guild=True)
    @commands.guild_only()
    async def setcoins(self, ctx):
        """Admin settings for coins."""
        pass

    @setcoins.command(name="amount")
    async def setcoins_amount(self, ctx: commands.Context, amount: int):
        """Set the amount of coins members can obtain.
        If 0, members will get a random amount."""
        if amount < 0:
            return await ctx.send("Uh oh, the amount cannot be negative.")
        if self._max_balance_check(amount):
            return await ctx.send(
                f"Uh oh, you can't set an amount of coins greater than {_MAX_BALANCE:,}."
            )
        await self.config.guild(ctx.guild).amount.set(amount)
        if amount != 0:
            await ctx.send(f"Members will receive {amount} coins.")
        else:
            pred = MessagePredicate.valid_int(ctx)
            await ctx.send("What's the minimum amount of coins members can obtain?")
            try:
                await self.bot.wait_for("message", timeout=30, check=pred)
            except asyncio.TimeoutError:
                return await ctx.send("You took too long. Try again, please.")
            minimum = pred.result
            await self.config.guild(ctx.guild).minimum.set(minimum)

            await ctx.send("What's the maximum amount of coins members can obtain?")
            try:
                await self.bot.wait_for("message", timeout=30, check=pred)
            except asyncio.TimeoutError:
                return await ctx.send("You took too long. Try again, please.")
            maximum = pred.result
            await self.config.guild(ctx.guild).maximum.set(maximum)

            await ctx.send(
                f"Members will receive a random amount of coins between {minimum} and {maximum}."
            )

    @setcoin.command(name="cooldown", aliases=["cd"])
    async def setcoin_cd(self, ctx: commands.Context, seconds: int):
        """Set the cooldown for `[p]coin`.
        This is in seconds! Default is 86400 seconds (24 hours)."""
        if seconds <= 0:
            return await ctx.send("Uh oh, cooldown has to be more than 0 seconds.")
        await self.config.guild(ctx.guild).cooldown.set(seconds)
        await ctx.send(f"Set the cooldown to {seconds} seconds.")

    @setcoin.command(name="stealcooldown", aliases=["stealcd"])
    async def setcoin_stealcd(self, ctx: commands.Context, seconds: int):
        """Set the cooldown for `[p]steal`.
        This is in seconds! Default is 43200 seconds (12 hours)."""
        if seconds <= 0:
            return await ctx.send("Uh oh, cooldown has to be more than 0 seconds.")
        await self.config.guild(ctx.guild).stealcd.set(seconds)
        await ctx.send(f"Set the cooldown to {seconds} seconds.")

    @setcoin.command(name="steal")
    async def setcoin_steal(self, ctx: commands.Context, on_off: bool = None):
        """Toggle coin stealing for current server. 
        If `on_off` is not provided, the state will be flipped."""
        target_state = (
            on_off
            if on_off
            else not (await self.config.guild(ctx.guild).stealing())
        )
        await self.config.guild(ctx.guild).stealing.set(target_state)
        if target_state:
            await ctx.send("Stealing is now enabled.")
        else:
            await ctx.send("Stealing is now disabled.")

    @setcoins.command(name="set")
    async def setcoins_set(
        self, ctx: commands.Context, target: discord.Member, amount: int
    ):
        """Set someone's amount of coins."""
        if amount <= 0:
            return await ctx.send("Uh oh, amount has to be more than 0.")
        if self._max_balance_check(amount):
            return await ctx.send(
                f"Uh oh, amount can't be greater than {_MAX_BALANCE:,}."
            )
        await self.config.member(target).coins.set(amount)
        await ctx.send(f"Set {target.mention}'s balance to {amount} :cookie:")

    @setcoins.command(name="add")
    async def setcoins_add(
        self, ctx: commands.Context, target: discord.Member, amount: int
    ):
        """Add coins to someone."""
        if amount <= 0:
            return await ctx.send("Uh oh, amount has to be more than 0.")
        target_coins = int(await self.config.member(target).coins())
        target_coins += amount
        if self._max_balance_check(target_coins):
            return await ctx.send(
                f"Uh oh, {target.display_name} has reached the maximum amount of coins."
            )
        await self.config.member(target).coins.set(target_coins)
        await ctx.send(f"Added {amount} :cookie: to {target.mention}'s balance.")

    @setcoins.command(name="take")
    async def setcoins_take(
        self, ctx: commands.Context, target: discord.Member, amount: int
    ):
        """Take coins away from someone."""
        if amount <= 0:
            return await ctx.send("Uh oh, amount has to be more than 0.")
        target_coins = int(await self.config.member(target).coins())
        if amount <= target_coins:
            target_coins -= amount
            await self.config.member(target).coins.set(target_coins)
            await ctx.send(
                f"Took away {amount} :cookie: from {target.mention}'s balance."
            )
        else:
            await ctx.send(f"{target.mention} doesn't have enough :cookies:")

    @setcoins.command(name="reset")
    async def setcoins_reset(self, ctx: commands.Context, confirmation: bool = False):
        """Delete all coins from all members."""
        if not confirmation:
            return await ctx.send(
                "This will delete **all** coins from all members. This action **cannot** be undone.\n"
                f"If you're sure, type `{ctx.clean_prefix}setcoins reset yes`."
            )
        for member in ctx.guild.members:
            coins = int(await self.config.member(member).coins())
            if coins != 0:
                await self.config.member(member).coins.set(0)
        await ctx.send("All coins have been deleted from all members.")

    @setcoins.command(name="rate")
    async def setcoins_rate(self, ctx: commands.Context, rate: Union[int, float]):
        """Set the exchange rate for `[p]coinexchange`."""
        if rate <= 0:
            return await ctx.send("Uh oh, rate has to be more than 0.")
        await self.config.guild(ctx.guild).rate.set(rate)
        currency = await bank.get_currency_name(ctx.guild)
        test_amount = 100*rate
        await ctx.send(f"Set the exchange rate {rate}. This means that 100 {currency} will give you {test_amount} :cookie:")

    @setcoins.group(autohelp=True)
    async def role(self, ctx):
        """Coin rewards for roles."""
        pass

    @role.command(name="add")
    async def setcoins_role_add(
        self, ctx: commands.Context, role: discord.Role, amount: int
    ):
        """Set coins for role."""
        if amount <= 0:
            return await ctx.send("Uh oh, amount has to be more than 0.")
        await self.config.role(role).coins.set(amount)
        await ctx.send(f"Gaining {role.name} will now give {amount} :cookie:")

    @role.command(name="del")
    async def setcoins_role_del(self, ctx: commands.Context, role: discord.Role):
        """Delete coins for role."""
        await self.config.role(role).coins.set(0)
        await ctx.send(f"Gaining {role.name} will now not give any :cookie:")

    @role.command(name="show")
    async def setcoins_role_show(self, ctx: commands.Context, role: discord.Role):
        """Show how many coins a role gives."""
        coins = int(await self.config.role(role).coins())
        await ctx.send(f"Gaining {role.name} gives {coins} :cookie:")

    @role.command(name="multiplier")
    async def setcoins_role_multiplier(
        self, ctx: commands.Context, role: discord.Role, multiplier: int
    ):
        """Set coins multipler for role. Disabled when random amount is enabled.
        
        Default is 1 (aka the same amount)."""
        if multiplier <= 0:
            return await ctx.send("Uh oh, multiplier has to be more than 0.")
        await self.config.role(role).multiplier.set(multiplier)
        await ctx.send(f"Users with {role.name} will now get {multiplier} times more :cookie:")

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        b = set(before.roles)
        a = set(after.roles)
        after_roles = [list(a - b)][0]
        if after_roles:
            for role in after_roles:
                coins = int(await self.config.role(role).coins())
                if coins != 0:
                    old_coins = int(await self.config.member(after).coins())
                    new_coins = old_coins + coins
                    if self._max_balance_check(new_coins):
                        continue
                    await self.config.member(after).coins.set(new_coins)

    async def _get_ids(self, ctx):
        data = await self.config.all_members(ctx.guild)
        ids = sorted(data, key=lambda x: data[x]["coins"], reverse=True)
        return ids

    @staticmethod
    def display_time(seconds, granularity=2):
        intervals = (  # Source: from economy.py
            (("weeks"), 604800),  # 60 * 60 * 24 * 7
            (("days"), 86400),  # 60 * 60 * 24
            (("hours"), 3600),  # 60 * 60
            (("minutes"), 60),
            (("seconds"), 1),
        )

        result = []

        for name, count in intervals:
            value = seconds // count
            if value:
                seconds -= value * count
                if value == 1:
                    name = name.rstrip("s")
                result.append(f"{value} {name}")
        return ", ".join(result[:granularity])

    @staticmethod
    def _max_balance_check(value: int):
        if value > _MAX_BALANCE:
            return True