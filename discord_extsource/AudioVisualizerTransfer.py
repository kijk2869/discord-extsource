from typing import Any
import discord
import numpy

from .PyAVSource import PyAVSource


class AudioVisualizerTransfer(discord.AudioSource):
    def __init__(self, original: discord.AudioSource) -> None:
        if not isinstance(original, PyAVSource):
            raise TypeError

        self.original = original
        self.VisualizerArray = [0.0] * 16

    @property
    def visualize(self) -> str:
        return "\n".join(
            map(
                lambda x: "|" * (round(x.item()) - 30) if x else "",
                self.VisualizerArray,
            )
        )

    def __getattr__(self, key: str) -> Any:
        return getattr(self.original, key)

    def cleanup(self) -> None:
        return self.original.cleanup()

    def is_opus(self) -> bool:
        return False

    def read(self) -> bytes:
        PCM = self.original.read()

        data = numpy.fromstring(PCM, dtype="int16")[0:960][::1] * numpy.hanning(960)
        paddedData = numpy.pad(data, (0, 1088), "constant")
        spectrum = numpy.fft.fft(paddedData)
        y = 20 * numpy.log10(abs(spectrum[0:1023]))
        y[numpy.isinf(y)] = 0

        self.VisualizerArray = [
            sum(y[(i - 1) * 64 : i * 64]) / 64 if i else y[0]
            for i in range(round(len(y) / 64))
        ]

        return PCM
