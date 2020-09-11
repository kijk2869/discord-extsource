import audioop
import queue

import discord

from .PyAVSource import PyAVSource


class CrossfadePlayer(discord.AudioSource):
    def __init__(self, *args) -> None:
        self._volume = 1.0
        self._crossfade = 10.0
        self.DELAY = 0.02

        self.Queue = queue.Queue()

        for Item in args:
            self.Queue.put_nowait(Item)

        self._waiting = self._playing = None

    def read(self) -> bytes:
        if self.Queue.empty() and not self._playing and not self._waiting:
            return

        if not self._waiting and not self.Queue.empty():
            self._waiting = self.Queue.get_nowait()
            self._waiting.start()

        if not self._playing:
            self._playing = self._waiting
            self._waiting = None

        Data = self._playing.read()

        if not Data:
            self._playing = None
            return self.read()

        if (
            self._waiting
            and self._playing.duration
            and self._playing.position >= (self._playing.duration - self._crossfade)
        ):
            NextData = self._waiting.read()

            CrossFadeVolume = 1.0 / (self.crossfade / self.DELAY)
            if self._waiting.volume < 1.0:
                self._waiting.volume = round(self._waiting.volume + CrossFadeVolume, 10)
            if self._playing.volume > 0.0:
                self._playing.volume = round(self._playing.volume - CrossFadeVolume, 10)

            Data = audioop.add(Data, NextData, 2)
        else:
            if self._playing.volume < 1.0:
                self._playing.volume = round(self._playing.volume + 0.01, 3)
            if self._waiting and self._waiting.volume != 0.0:
                self._waiting.volume == 0.0

        if self._volume != 1.0:
            Data = audioop.mul(Data, 2, min(self._volume, 2.0))

        return Data

    def cleanup(self) -> None:
        if self._playing:
            self._playing.cleanup()
        if self._waiting:
            self._waiting.cleanup()

        for Item in self.Queue.queue:
            Item.cleanup()

    def is_opus(self) -> bool:
        return False

    def put(self, Item) -> None:
        return self.Queue.put_nowait(Item)

    def skip(self) -> None:
        self._playing = None

    def seek(self, *args, **kwargs) -> None:
        if not self._playing:
            raise ValueError

        return self._playing.seek(*args, **kwargs)

    @property
    def crossfade(self) -> float:
        return self._crossfade

    @crossfade.setter
    def crossfade(self, value: float) -> None:
        self._crossfade = value

    @property
    def volume(self) -> float:
        return self._volume

    @volume.setter
    def volume(self, value: float) -> None:
        self._volume = max(value, 0.0)

    @property
    def current(self) -> PyAVSource:
        return self._playing
