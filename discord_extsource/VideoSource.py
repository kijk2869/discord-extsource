import asyncio
import queue
import time
import traceback
import av
import io
import threading

import discord

from .PyAVSource import PyAVSource


class VideoSource(PyAVSource):
    def __init__(
        self,
        channel: discord.TextChannel,
        *args,
        limit: int = 5,
        quality: int = 50,
        **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)

        self.prev_message = None
        self.channel = channel

        self.VideoContainer = None  # av.StreamContainer
        self.selectVideoStream = self.VideoFrameGenerator = None

        self.ScreenShots = queue.Queue(maxsize=limit)
        self.quality = quality
        self.send_task = None

    async def __send(self, *args, **kwargs) -> None:
        Count = time.perf_counter()

        to_delete = self.prev_message

        self.prev_message = await self.channel.send(*args, **kwargs)

        if to_delete:
            try:
                await to_delete.delete()
            except:
                pass

        delay = 1 - (time.perf_counter() - Count)
        await asyncio.sleep(delay)

    def read(self) -> bytes:
        Data = super().read()

        if not self.ScreenShots.empty() and (
            not self.send_task or self.send_task.done()
        ):
            if self.ScreenShots.queue[0][0] <= self.position:
                FilteredScreenShots = [
                    ScreenShot
                    for ScreenShot in self.ScreenShots.queue
                    if ScreenShot[0] <= self.position
                ]

                position, Image = FilteredScreenShots[-1]

                File = discord.File(Image, filename="video.png")

                self.send_task = self.loop.create_task(self.__send(file=File))

                for ScreenShot in FilteredScreenShots:
                    self.ScreenShots.get_nowait()

        return Data

    def _seek(self, *args, **kwargs) -> None:
        raise NotImplementedError

    def reload(self) -> None:
        raise NotImplementedError

    def start(self) -> None:
        self.VideoLoader = Loader(self)
        self.VideoLoader.start()

        return super().start()

    def cleanup(self) -> None:
        self.ScreenShots.queue.clear()

        return super().cleanup()


class Loader(threading.Thread):
    def __init__(self, Source: VideoSource) -> None:
        threading.Thread.__init__(self)
        self.daemon = True

        self.Source = Source

    def __do_run(self) -> None:
        if not self.Source.VideoContainer:
            self.Source.VideoContainer = av.open(
                self.Source.Source, options=self.Source.AVOption
            )

        self.Source.selectVideoStream = self.Source.VideoContainer.streams.video[0]
        self.Source.selectVideoStream.codec_context.skip_frame = "NONKEY"
        self.Source.VideoFrameGenerator = self.Source.VideoContainer.decode(
            self.Source.selectVideoStream
        )

        prev_position = None
        while not self.Source._end.is_set():
            Frame = next(self.Source.VideoFrameGenerator, None)

            if not Frame:
                break

            Position = int(Frame.pts * Frame.time_base)
            if Position == prev_position:
                continue

            prev_position = Position

            fp = io.BytesIO()
            Frame.to_image().save(fp, format="png", quality=self.Source.quality)
            fp.seek(0)

            self.Source.ScreenShots.put([Position, fp])

    def run(self):
        try:
            self.__do_run()
        except:
            traceback.print_exc()
        finally:
            if self.Source.VideoContainer:
                self.Source.VideoContainer.close()
                self.Source.VideoContainer = None