from youtube_dl import extractor

from discord_extsource.exceptions import NotSeekable

from .extractor import extract
from .PyAVSource import PyAVSource


class YTDLSource(PyAVSource):
    def __init__(self, Data: dict, *args, **kwargs) -> None:
        super().__init__(Data["url"], *args, **kwargs)

        self.Data = Data

    def __getattr__(self, key: str) -> str:
        return self.Data[key]

    @classmethod
    async def create(cls, Query: str, *args, **kwargs):
        Data = await extract(Query)

        if isinstance(Data, list):
            Data = Data[0]

        return cls(Data, *args, **kwargs)

    def seek(self, *args, **kwargs) -> None:
        if not self.is_live:
            raise NotSeekable

        return super().seek(*args, **kwargs)
