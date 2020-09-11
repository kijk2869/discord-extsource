import discord

from .PyAVSource import PyAVSource


class FadedVolumeTransfer(discord.AudioSource):
    def __init__(self, original: discord.AudioSource, volume: float = 1.0) -> None:
        if not isinstance(original, PyAVSource):
            raise TypeError

        self.original = original
        self.original.volume = self._volume = volume

    @property
    def volume(self) -> None:
        return self._volume

    @volume.setter
    def volume(self, value: float) -> None:
        self._volume = value

    def cleanup(self) -> None:
        return self.original.cleanup()

    def is_opus(self) -> bool:
        return False

    def read(self) -> bytes:
        if self.original.volume != self.volume:
            if self.original.volume < self.volume:
                self.original.volume = round(self.original.volume + 0.01, 3)
            elif self.original.volume > self.volume:
                self.original.volume = round(self.original.volume - 0.01, 3)

        return self.original.read()
