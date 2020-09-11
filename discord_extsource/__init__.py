from .AudioFifo import AudioFifo
from .exceptions import *
from .extractor import *
from .PyAVSource import PyAVSource
from .utils import *
from .YTDLSource import YTDLSource
from .GaplessPlayer import GaplessPlayer
from .YTDLVideoSource import YTDLVideoSource
from .VideoSource import VideoSource


# def __patch_opus():
#     import discord.opus

#     class Encoder(discord.opus.Encoder):
#         def __init__(self, *args, **kwargs):
#             super().__init__(self, *args, **kwargs)

#             self.set_expected_packet_loss_percent(0)

#     discord.opus.Encoder = Encoder


# __patch_opus()