import asyncio
from xml.etree import ElementTree

import discord
from aiohttp import ClientSession
from markdownify import markdownify

from .PyAVSource import PyAVSource
from .YTDLSource import YTDLSource
from .YTDLVideoSource import YTDLVideoSource


class srv1:
    def __init__(self, Tree: ElementTree) -> None:
        self.Tree = Tree

        self.TextElements = {
            float(TextElement.attrib["start"]): {
                "start": float(TextElement.attrib["start"]),
                "duration": float(TextElement.attrib["dur"]),
                "end": round(
                    float(TextElement.attrib["start"])
                    + float(TextElement.attrib["dur"]),
                    2,
                ),
                "text": TextElement.text,
                "markdown": markdownify(TextElement.text),
            }
            for TextElement in self.Tree.findall("text")
        }

        self.duration = sorted(
            [TextElement["end"] for TextElement in self.TextElements.values()]
        )[-1]

        self.time = 0.0
        self.current = None

    @classmethod
    async def load(cls, URL: str):
        async with ClientSession() as session:
            async with session.get(URL) as session:
                Data = await session.text()

        Tree = ElementTree.fromstring(Data)
        return cls(Tree)

    def seek(self, time: float) -> str:
        self.time = float(time)

        if (
            not self.current
            or not self.current["start"] <= self.time < self.current["end"]
        ):
            Elements = [
                TextElement
                for Start, TextElement in self.TextElements.items()
                if Start <= self.time < TextElement["end"]
            ]
            self.current = Elements[-1] if Elements else None

        return self.lyrics

    def __dict__(self) -> dict:
        return self.TextElements

    @property
    def lyrics(self) -> str:
        if self.current:
            return self.current
        return None

    @property
    def is_done(self) -> bool:
        return self.time >= self.duration


class Lyrics:
    def __init__(self, Source: PyAVSource, language: str) -> None:
        if not isinstance(Source, (YTDLSource, YTDLVideoSource)):
            raise TypeError

        self.loop = asyncio.get_event_loop()

        self.Source = Source
        self.srv1_list = (
            {
                lang: [
                    LyricsData["url"]
                    for LyricsData in lyrics
                    if LyricsData["ext"] == "srv1"
                ][0]
                for lang, lyrics in Source.subtitles.items()
            }
            if "subtitles" in Source.Data
            else {}
        )

        self.srv1_url = self.srv1_list[language]

        self.channel = None

    def start(self) -> None:
        self.loop.create_task(self._task())

    def subcribe(self, channel: discord.TextChannel) -> None:
        self.channel = channel
        self.start()

    def unsubcribe(self) -> None:
        self.channel = None

    def _safe_delete(self, message: discord.Message, *args, **kwargs) -> None:
        return message.delete(*args, **kwargs)

    def _safe_edit(self, message: discord.Message, *args, **kwargs) -> discord.Message:
        return message.edit(*args, **kwargs)

    async def _task(self):
        self.Lyrics = await srv1.load(self.srv1_url)

        _message = _Previous = _Now = _Next = None
        Elements = list(self.Lyrics.TextElements.values())
        while not self.Lyrics.is_done and not self.Source._end.is_set():
            if not self.channel:
                return

            Element = self.Lyrics.seek(self.Source.position)

            if Element and Element["markdown"] and Element["markdown"] != _Now:
                _Previous = _Now
                _Now = Element["markdown"]

                NextElements = [
                    NextElement["markdown"]
                    for NextElement in Elements[Elements.index(Element) + 1 :]
                    if NextElement["markdown"] != _Now
                ]

                _Next = NextElements[0] if NextElements else None

                Text = (
                    (f"{_Previous}\n" if _Previous else "")
                    + "> "
                    + _Now.replace("\n", "\n> ")
                    + (f"\n{_Next}" if _Next else "")
                )

                if not _message or _message.id != self.channel.last_message_id:
                    if _message:
                        self.loop.create_task(self._safe_delete(_message))
                    _message = await self.channel.send(Text)
                else:
                    await self._safe_edit(_message, content=Text)

            await asyncio.sleep(0.1)
