from discord.ext import commands

class Admin:
    def __init__(self, bot):
        self.bot = bot

    @commands.is_owner()
    @commands.command()
    async def stop(self, ctx):
        await ctx.send("Shutting down.")
        await self.bot.close()
