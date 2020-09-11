from .AudioFifo import AudioFifo
from .CrossfadePlayer import CrossfadePlayer
from .exceptions import *
from .extractor import *
from .FadedVolumeTransfer import FadedVolumeTransfer
from .GaplessPlayer import GaplessPlayer
from .PyAVSource import PyAVSource
from .utils import *
from .VideoSource import VideoSource
from .YTDLSource import YTDLSource
from .YTDLVideoSource import YTDLVideoSource

# def __patch_opus():
#     import discord.opus

#     class Encoder(discord.opus.Encoder):
#         def __init__(self, *args, **kwargs):
#             super().__init__(self, *args, **kwargs)

#             self.set_expected_packet_loss_percent(0)

#     discord.opus.Encoder = Encoder


# __patch_opus()
