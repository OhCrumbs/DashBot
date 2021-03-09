from .coins import Coins


def setup(bot):
    bot.add_cog(Coins(bot))