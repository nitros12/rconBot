from collections import defaultdict
from asyncio import Lock


def ddict(*args, **kwargs):
    return defaultdict(ddict, *args, **kwargs)


def build_ddict(d):
    def b(value):
        if isinstance(value, dict):
            return build_ddict(value)
        return value
    return ddict((k, b(v)) for k, v in d.items())


def build_dict(d):
    def b(value):
        if isinstance(value, defaultdict):
            return build_dict(value)
        return value
    return dict((k, b(v)) for k, v in d.items())


class Config:
    def __init__(self, fname: str, decoder):
        self.decoder = decoder
        self.fname = fname
        self.lock = Lock()
        self._load()

    def __getitem__(self, item):
        return self.data[str(item)]

    def __setitem__(self, key, value):
        self.data[str(key)] = value

    def _load(self):
        with open(self.fname) as fp:
            self.data = build_ddict(self.decoder.load(fp))

    async def load(self):
        async with self.lock:
            self._load()

    def _save(self):
        with open(self.fname, "w") as fp:
            self.decoder.dump(build_dict(self.data), fp)

    async def save(self):
        async with self.lock:
            self._save()

    def get(self, *args, **kwargs):
        return self.data.get(*args, **kwargs)
