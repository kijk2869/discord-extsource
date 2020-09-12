import asyncio
from xml.etree import ElementTree

import discord
from aiohttp import ClientSession
from discord.channel import TextChannel
from google.protobuf.duration_pb2 import Duration
from markdownify import markdownify
import re

from .PyAVSource import PyAVSource
from .YTDLSource import YTDLSource
from .YTDLVideoSource import YTDLVideoSource


class LyricsFormat:
    def __init__(self) -> None:
        self.time = 0.0
        self.current = None

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


class smi(LyricsFormat):
    BODY_REGEX = re.compile(r"<body>([\w|\W|\s]+)</body>", flags=re.I)
    SYNC_REGEX = re.compile(r"<Sync Start=([0-9]+)>([\s|\w|\W]+)", flags=re.I)

    def __init__(self, Body: str) -> None:
        super().__init__()

        self._TextElements = []

        for Text in [
            Item.strip()
            for Item in self.BODY_REGEX.search(Body).group(1).splitlines()
            if Item.strip()
        ]:
            if Text.lower().startswith("<sync"):
                Match = self.SYNC_REGEX.match(Text)

                Start, Element = round(int(Match.group(1)) / 1000, 2), Match.group(2)

                if self._TextElements:
                    self._TextElements[-1]["end"] = Start - 1
                    self._TextElements[-1]["duration"] = (
                        self._TextElements[-1]["end"] - self._TextElements[-1]["start"]
                    )

                self._TextElements.append({"start": Start, "text": Element})
            else:
                self._TextElements[-1]["text"] += "\n" + Text

        self.TextElements = {
            TextElement["start"]: dict(
                TextElement,
                markdown=markdownify(TextElement["text"]).strip(),
                end=TextElement.get("end") or TextElement["start"] + 5,
                duration=TextElement.get("duration") or 5,
            )
            for TextElement in self._TextElements
            if markdownify(TextElement["text"]).strip()
        }

        self.duration = sorted(
            [TextElement["end"] for TextElement in self.TextElements.values()]
        )[-1]

    @classmethod
    async def load(cls, URL: str):
        async with ClientSession() as session:
            async with session.get(URL) as session:
                Data = await session.text()

        return cls(Data)


class srv1(LyricsFormat):
    def __init__(self, Tree: ElementTree) -> None:
        super().__init__()

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

    @classmethod
    async def load(cls, URL: str):
        async with ClientSession() as session:
            async with session.get(URL) as session:
                Data = await session.text()

        Tree = ElementTree.fromstring(Data)
        return cls(Tree)


class Lyrics:
    def __init__(self, Source: PyAVSource, url: str, type: str = "srv1") -> None:
        self.loop = asyncio.get_event_loop()

        self.Source = Source
        self.url = url

        if self.url.endswith(".smi"):
            self.type = "smi"

        self.channel = None

    @classmethod
    def from_source(cls, Source: PyAVSource, language: str):
        if not isinstance(Source, (YTDLSource, YTDLVideoSource)):
            raise TypeError

        cls.srv1_list = (
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

        cls.srv1_url = cls.srv1_list[language]

        return cls(Source, cls.srv1_url, type="srv1")

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
        if self.type == "srv1":
            self.Lyrics = await srv1.load(self.url)
        elif self.type == "smi":
            self.Lyrics = await smi.load(self.url)

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
