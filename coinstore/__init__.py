from .coinstore import CoinStore


def setup(bot):
    bot.add_cog(CoinStore(bot))