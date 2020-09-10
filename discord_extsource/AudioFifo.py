import threading

import av


class AudioFifo(av.AudioFifo):
    def __init__(self, BufferLimit: int = 5, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.AUDIOBUFFERLIMITMS = BufferLimit * 50 * 960

        self.haveToFillBuffer = threading.Event()
        self.haveToFillBuffer.set()

    def read(self, samples: int = 960) -> bytes:

        AudioFrame = super().read(samples)
        if not AudioFrame:
            return

        if self.samples < self.AUDIOBUFFERLIMITMS:
            self.haveToFillBuffer.set()
        else:
            self.haveToFillBuffer.clear()

        return AudioFrame.planes[0].to_bytes()

    def write(self, *args, **kwargs):
        super().write(*args, **kwargs)

        if self.samples < self.AUDIOBUFFERLIMITMS:
            self.haveToFillBuffer.set()
        else:
            self.haveToFillBuffer.clear()

    def reset(self):
        super().read(samples=max(self.samples - 960, 0), partial=True)
