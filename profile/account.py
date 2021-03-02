from redbot.core import checks, Config
from redbot.core.i18n import Translator, cog_i18n
import discord
from redbot.core import commands
from redbot.core.utils import mod
import asyncio
import datetime

class Account(commands.Cog):
    """The Profile Cog"""

    def __init__(self, bot):
        self.bot = bot
        default_member = {
            "Driver_Number": None,
            "TMP_profile": None,
            "Gender": None,
            "Job": None,
            "Email": None,
            "Country": None,
            "Age": None,
            "Characterpic": None
        }
        default_guild = {
            "db": []
        }
        self.config = Config.get_conf(self, identifier=42)
        self.config.register_guild(**default_guild)
        self.config.register_member(**default_member)
    
    @commands.command(name="signup")
    @commands.guild_only()
    async def _reg(self, ctx):
        """Become a driver to get your own profile!"""

        server = ctx.guild
        user = ctx.author
        db = await self.config.guild(server).db()
        if user.id not in db:
            db.append(user.id)
            await self.config.guild(server).db.set(db)
            data = discord.Embed(colour=user.colour)
            data.add_field(name="Congrats!:sparkles:", value="You have officially created your profile for **{}**, {}.".format(server.name, user.mention))
            await ctx.send(embed=data)
        else: 
            data = discord.Embed(colour=user.colour)
            data.add_field(name="Error:warning:",value="Oops, it seems like you already have a profile, {}.".format(user.mention))
            await ctx.send(embed=data)
        
    
    @commands.command(name="account")
    @commands.guild_only()
    async def _acc(self, ctx, user : discord.Member=None):
        """Your/Others Profile"""
                    
        server = ctx.guild
        db = await self.config.guild(server).db()
        user = user if user else ctx.author
        userdata = await self.config.member(user).all()
        pic = userdata["Characterpic"]
        
        data = discord.Embed(description="{}".format(server), colour=user.colour)
        fields = [data.add_field(name=k, value=v) for k,v in userdata.items() if v and not k == "Characterpic"] ##let's not add image url to the embed, would look bad
        
        if user.avatar_url and not pic:
            name = str(user)
            name = " ~ ".join((name, user.nick)) if user.nick else name
            data.set_author(name=name, url=user.avatar_url)
            data.set_thumbnail(url=user.avatar_url)
        elif pic:
            data.set_author(name=user.name, url=user.avatar_url)
            data.set_thumbnail(url=pic)
        else:
            data.set_author(name=user.name)
        
        if len(fields) != 0:
            await ctx.send(embed=data)
        else:
            data = discord.Embed(colour=user.colour)
            data.add_field(name="Error:warning:",value="{} doesn't have a profile at the moment, sorry.".format(user.mention))
            await ctx.send(embed=data)

    @commands.group(name="update")
    @commands.guild_only()
    async def update(self, ctx):
        """Update your profile!"""
        pass

    @update.command(pass_context=True)
    @commands.guild_only()
    async def age(self, ctx, *, age):
        """Tell us about yourself"""
        
        server = ctx.guild
        user = ctx.author
        prefix = ctx.prefix
        db = await self.config.guild(server).db()
        
        if user.id not in db:
            data = discord.Embed(colour=user.colour)
            data.add_field(name="Error:warning:",value="This feature is only available for people who have a profile. \n\nTo get a profile you need to be a driver.".format(prefix))
            await ctx.send(embed=data)
        else:
            await self.config.member(user).Age.set(age)
            data = discord.Embed(colour=user.colour)
            data.add_field(name="Congrats!:sparkles:",value="You have updated your About Me to {}".format(age))
            await ctx.send(embed=data)

    @update.command(pass_context=True)
    @commands.guild_only()
    async def tmp_profile(self, ctx, *, profile):
        """TruckersMP Profile?"""
        
        server = ctx.guild
        user = ctx.message.author
        prefix = ctx.prefix
        db = await self.config.guild(server).db()

        if user.id not in db:
            data = discord.Embed(colour=user.colour)
            data.add_field(name="Error:warning:",value="This feature is only available for people who have a profile. \n\nTo get a profile you need to be a driver.".format(prefix))
            await ctx.send(embed=data)
        else:
            await self.config.member(user).TMP_Profile.set(profile)
            data = discord.Embed(colour=user.colour)
            data.add_field(name="Congrats!:sparkles:",value="You have set your TMP profile to {}".format(profile))
            await ctx.send(embed=data)

    @update.command(pass_context=True)
    @commands.guild_only()
    async def drivernumber(self, ctx, *, number):
        """What's your driver number?"""
        
        server = ctx.guild
        user = ctx.author
        prefix = ctx.prefix
        db = await self.config.guild(server).db()

        if user.id not in db:
            data = discord.Embed(colour=user.colour)
            data.add_field(name="Error:warning:",value="This feature is only available for people who have a profile. \n\nTo get a profile you need to be a driver.".format(prefix))
            await ctx.send(embed=data)
        else:
            await self.config.member(user).Driver_Number.set(number)
            data = discord.Embed(colour=user.colour)
            data.add_field(name="Congrats!:sparkles:",value="You have set your driver number to {}".format(number))
            await ctx.send(embed=data)

    @update.command(pass_context=True)
    @commands.guild_only()
    async def job(self, ctx, *, job):
        """Do you have a job?"""
        
        server = ctx.guild
        user = ctx.author
        prefix = ctx.prefix
        db = await self.config.guild(server).db()

        if user.id not in db:
            data = discord.Embed(colour=user.colour)
            data.add_field(name="Error:warning:",value="This feature is only available for people who have a profile. \n\nTo get a profile you need to be a driver.".format(prefix))
            await ctx.send(embed=data)
        else:
            await self.config.member(user).Job.set(job)
            data = discord.Embed(colour=user.colour)
            data.add_field(name="Congrats!:sparkles:",value="You have set your Job to {}".format(job))
            await ctx.send(embed=data)
    
    @update.command(pass_context=True)
    @commands.guild_only()
    async def gender(self, ctx, *, gender):
        """What's your gender?"""

        server = ctx.guild
        user = ctx.author
        prefix = ctx.prefix
        db = await self.config.guild(server).db()

        if user.id not in db:
            data = discord.Embed(colour=user.colour)
            data.add_field(name="Error:warning:",value="This feature is only available for people who have a profile. \n\nTo get a profile you need to be a driver.".format(prefix))
            await ctx.send(embed=data)
        else:
            await self.config.member(user).Gender.set(gender)
            data = discord.Embed(colour=user.colour)
            data.add_field(name="Congrats!:sparkles:",value="You have set your Gender to {}".format(gender))
            await ctx.send(embed=data)
 
    @update.command(pass_context=True)
    @commands.guild_only()
    async def email(self, ctx, *, email):
        """What's your email address?"""

        
        server = ctx.guild
        user = ctx.author
        prefix = ctx.prefix
        db = await self.config.guild(server).db()

        if user.id not in db:
            data = discord.Embed(colour=user.colour)
            data.add_field(name="Error:warning:",value="This feature is only available for people who have a profile. \n\nTo get a profile you need to be a driver.".format(prefix))
            await ctx.send(embed=data)
        else:
            await self.config.member(user).Email.set(email)
            data = discord.Embed(colour=user.colour)
            data.add_field(name="Congrats!:sparkles:",value="You have set your Email to {}".format(email))
            await ctx.send(embed=data)

    @update.command(pass_context=True)
    @commands.guild_only()
    async def country(self, ctx, *, country):
        """Which country do you live in?"""
        
        server = ctx.guild
        user = ctx.author
        prefix = ctx.prefix
        db = await self.config.guild(server).db()

        if user.id not in db:
            data = discord.Embed(colour=user.colour)
            data.add_field(name="Error:warning:",value="This feature is only available for people who have a profile. \n\nTo get a profile you need to be a driver.".format(prefix))
            await ctx.send(embed=data)
        else:
            await self.config.member(user).Country.set(country)
            data = discord.Embed(colour=user.colour)
            data.add_field(name="Congrats!:sparkles:",value="You have set your country to {}".format(country))
            await ctx.send(embed=data)
            
    @update.command(pass_context=True)
    @commands.guild_only()
    async def characterpic(self, ctx, *, characterpic):
        """What does your character look like?"""
        
        server = ctx.guild
        user = ctx.author
        prefix = ctx.prefix
        db = await self.config.guild(server).db()

        if user.id not in db:
            data = discord.Embed(colour=user.colour)
            data.add_field(name="Error:warning:",value="This feature is only available for people who have a profile. \n\nTo get a profile you need to be a driver.".format(prefix))
            await ctx.send(embed=data)
        else:
            await self.config.member(user).Characterpic.set(characterpic)
            data = discord.Embed(colour=user.colour)
            data.add_field(name="Congrats!:sparkles:",value="You have set your characterpic to {}".format(characterpic))
            data.set_image(url="{}".format(characterpic))
            await ctx.send(embed=data)
