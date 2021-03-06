from ruamel.yaml import YAML

from discord.ext import commands

from conf import Config

base_cogs = ('cogs.rcon', 'cogs.admin')


class RconBot(commands.Bot):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.config = Config("config.yaml", YAML(typ="safe"))

        for i in base_cogs:
            self.load_extension(i)
            #  if we fail, throw an error on bot creation
