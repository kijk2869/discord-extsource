import audioop
from typing import Tuple, List
from .PyAVSource import PyAVSource
import discord


class Mixer(discord.AudioSource):
    def __init__(self) -> None:
        self._volume: float = 1.0
        self._VOLUME_PER_SOURCE: float = 1.0

        self._Tracks: List[PyAVSource] = []

    def __del__(self):
        self.cleanup()

    @property
    def volume(self) -> float:
        return self._volume

    @volume.setter
    def volume(self, value: float) -> None:
        self._volume = max(value, 0.0)

    @property
    def Tracks(self) -> List[Tuple[int, PyAVSource]]:
        return list(enumerate(self._Tracks))

    @property
    def VOLUME_PER_SOURCE(self) -> float:
        calculatedValue: float = round(max(100 / len(self._Tracks), 10) / 100, 2)

        if self._VOLUME_PER_SOURCE != calculatedValue:
            if self._VOLUME_PER_SOURCE < calculatedValue:
                self._VOLUME_PER_SOURCE = round(self._VOLUME_PER_SOURCE + 0.01, 3)
            elif self._VOLUME_PER_SOURCE > calculatedValue:
                self._VOLUME_PER_SOURCE = round(self._VOLUME_PER_SOURCE - 0.01, 3)

        return 1.0

    def addTrack(self, Source: PyAVSource) -> int:
        """Add track into mixer, returns Track number."""

        if Source in self._Tracks:
            raise ValueError("Already added.")

        if not Source.BufferLoader:
            Source.start()

        self._Tracks.append(Source)

        return self._Tracks.index(Source)

    def removeTrack(self, index: int) -> None:
        """Remove track from mixxer, returns None"""

        self._Tracks[index].cleanup()
        del self._Tracks[index]

        return None

    def read(self) -> bytes:
        PCM: bytes = None

        DONE_SOURCES: List[int] = []
        for index, Source in self.Tracks:
            if len(self.Tracks) != 1 and Source.AudioFifo.samples < 960:
                continue

            Data: bytes = Source.read()

            if not Data:
                DONE_SOURCES.append(index)
                continue

            Data = audioop.mul(Data, 2, min(self.VOLUME_PER_SOURCE, 2.0))

            PCM = audioop.add(PCM, Data, 2) if PCM is not None else Data

        for index in DONE_SOURCES:
            del self._Tracks[index]

        if self._volume != 1.0:
            PCM = audioop.mul(PCM, 2, min(self._volume, 2.0))
            
        return PCM

    def is_opus(self) -> bool:
        return False

    def cleanup(self) -> None:
        for Source in self._Tracks:
            try:
                Source.cleanup()
            except:
                continue