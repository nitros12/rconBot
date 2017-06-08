from discord.ext import commands

import asyncio_redis

base_cogs = ('cogs.rcon',)


class RconBot(commands.Bot):

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        for i in base_cogs:
            self.load_extension(i)
            #  if we fail, throw an error on bot creation

    async def start(self, *args, **kwargs):
        self.redis = await asyncio_redis.Connection.create(host='localhost', port=6379)
        await super().start(*args, **kwargs)

    async def close(self):
        await super().close()
        self.redis.close()
