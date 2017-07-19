import discord
from discord.ext import commands

from valve import rcon


def split_by_len(text: str, n: int) -> [str]:
    while text:
        yield text[:n]
        text = text[n:]


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

    async def run_rcon(self, conn, pw, command):
        conn = rcon.RCON(conn, pw)
        await self.bot.loop.run_in_executor(None, conn.connect)
        await self.bot.loop.run_in_executor(None, conn.authenticate)
        resp = await self.bot.loop.run_in_executor(None, conn.execute, command)
        text = resp.body.decode('utf-8')
        await self.bot.loop.run_in_executor(None, conn.close)
        return text

    async def handle_rcon(self, guild, name, command):
        key = f"{guild.id}:rcon_connections:{name}"
        coninfo = await self.bot.redis.hgetall_asdict(key)

        ip, port, pw = coninfo.values()
        return await self.run_rcon((ip, int(port)), pw, command)

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
        resp = await self.handle_rcon(ctx.guild, name, command)
        for i in split_by_len(resp, 1900):
            await ctx.send(f"```\n{i}```")

    @check_redis_roles()
    @commands.command(name="list")
    async def list_cmd(self, ctx):
        keys = await self.bot.redis.keys(f"{ctx.guild.id}:rcon_connections:*")
        split = [(await i).split(':')[-1] for i in keys]
        joined = "\n".join(split)
        await ctx.send(f"```\n{joined}```")

    @commands.has_permissions(administrator=True)
    @commands.command()
    async def set_default(self, ctx, name: str):
        """Set default connection to use for cmd command."""
        await self.bot.redis.set(f"{ctx.guild.id}:rcon_default", name)
        await ctx.send(f"Set default connection to {name}")

    @check_redis_roles()
    @commands.command()
    async def cmd(self, ctx, *, command: str):
        """Shortcut for command that uses default channel."""
        default = await self.bot.redis.get(f"{ctx.guild.id}:rcon_default")
        if default is None:
            await ctx.send("No default channel set, use set_default to use this!")
            return

        resp = await self.handle_rcon(ctx.guild, default, command)
        for i in split_by_len(resp, 1900):
            await ctx.send(f"```\n{i}```")

    @check_redis_roles()
    @commands.command()
    async def say(self, ctx, *, msg: str):
        """Helper command to send a message to the server."""
        default = await self.bot.redis.get(f"{ctx.guild.id}:rcon_default")
        if default is None:
            await ctx.send("No default channel set, use set_default to use this!")
            return

        cmd = f'say "{msg}"'
        resp = await self.handle_rcon(ctx.guild, default, cmd)
        for i in split_by_len(resp, 1900):
            await ctx.send(f"```\n{i}```")


def setup(bot):
    bot.add_cog(Rcon(bot))
