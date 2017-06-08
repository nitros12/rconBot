import discord
from discord.ext import commands

from valve import rcon


def check_redis_roles():
    async def predicate(ctx):
        if ctx.cog is None:
            return True  # for help command

        role_id = await ctx.bot.redis.get(f"{ctx.guild.id}:rcon_role")
        if role_id is None:  # added no rcon roles
            return False

        role = discord.utils.get(ctx.guild.roles, id=int(role_id))
        if role in ctx.author.roles:
            return True

        return False
    return commands.check(predicate)


class Rcon:

    def __init__(self, bot):
        self.rcon_sessions = {}
        self.bot = bot

    async def run_rcon(self, conn, command):
        conn = rcon.RCON(*conn)
        return await self.bot.loop.run_in_executor(None, conn, command)

    @commands.has_permissions(administrator=True)
    @commands.command()
    async def add_rcon(self, ctx, name: str, ip: str, port: int, pw: str):
        """Add a rcon address to the bot."""
        await self.bot.redis.hmset(f"{ctx.guild.id}:rcon_connections:{name}", dict(ip=ip, port=str(port), pw=pw))
        await ctx.send(f"Added rcon connection: {name}!")

    @commands.has_permissions(administrator=True)
    @commands.command()
    async def delete_rcon(self, ctx, name: str):
        """Delete a rcon address from the bot."""
        await self.bot.redis.delete(f"{ctx.guild.id}:rcon_connections:{name}")
        await ctx.send(f"Deleted rcon connection: {name}!")

    @commands.has_permissions(administrator=True)
    @commands.command()
    async def add_role(self, ctx, role: discord.Role):
        """Allow a role to list and command RCON connections.

        Note only one role is assigned per guild. Setting this when a role already is set will override.
        """
        await self.bot.redis.set(f"{ctx.guild.id}:rcon_role", str(role.id))
        await ctx.send(f"Set {role} as controlling rcon role for this guild!")

    @commands.has_permissions(administrator=True)
    @commands.command()
    async def delete_role(self, ctx):
        """Delete role for accessing rcon."""
        await self.bot.redis.delete([f"{ctx.guild.id}:rcon_role"])
        await ctx.send("Removed role controlling rcon role for this guild!")

    @check_redis_roles()
    @commands.command()
    async def command(self, ctx, name: str, *, command: str):
        """Send a rcon command to a connection and return the response."""
        key = f"{ctx.guild.id}:rcon_connections:{name}"

        coninfo = await self.bot.redis.hmget_aslist(key, (str, int, str))
        if coninfo is None:
            await ctx.send(f"{name} is not a valid rcon connection!")
            return

        *conn, pw = coninfo
        with ctx.channel.typing():
            resp = await self.run_rcon(conn, command)
            await ctx.send(f"```\n{resp}```")

    @check_redis_roles()
    @commands.command(name="list")
    async def list_cmd(self, ctx):
        keys = await self.bot.redis.keys(f"{ctx.guild.id}:rcon_connections:*")
        filtered = "\n".join((await i).split(':')[-1] for i in keys)
        await ctx.send(f"```\n{filtered}```")


def setup(bot):
    bot.add_cog(Rcon(bot))
