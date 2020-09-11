import discord
from youtube_dl import extractor

from discord_extsource.exceptions import NotSeekable

from .extractor import extract
from .VideoSource import VideoSource


class YTDLVideoSource(VideoSource):
    def __init__(
        self, Data: dict, channel: discord.TextChannel, *args, **kwargs
    ) -> None:
        super().__init__(channel, Data["url"], *args, **kwargs)

        self.Data = Data

    def __getattr__(self, key: str) -> str:
        return self.Data[key]

    @classmethod
    async def create(cls, Query: str, channel: discord.TextChannel, *args, **kwargs):
        Data = await extract(Query, video=True)

        if isinstance(Data, list):
            Data = Data[0]

        if not "url" in Data:
            return await cls.create(Data["id"], channel, *args, **kwargs)

        return cls(Data, channel, *args, **kwargs)
