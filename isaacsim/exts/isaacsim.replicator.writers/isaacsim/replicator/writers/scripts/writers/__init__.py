# Copyright (c) 2021-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

from .data_visualization_writer import *
from .dope_writer import *
from .pose_writer import *
from .pytorch_listener import *
from .pytorch_writer import *
from .ycb_video_writer import *


# Register writers and add them to the default writers for Replicator telemetry tracking
def register_writers():
    from omni.replicator.core import WriterRegistry

    # DataVisualizationWriter
    WriterRegistry.register(DataVisualizationWriter)
    WriterRegistry._default_writers.append(
        "DataVisualizationWriter"
    ) if "DataVisualizationWriter" not in WriterRegistry._default_writers else None

    # DOPEWriter
    WriterRegistry.register(DOPEWriter)
    WriterRegistry._default_writers.append(
        "DOPEWriter"
    ) if "DOPEWriter" not in WriterRegistry._default_writers else None

    # PoseWriter
    WriterRegistry.register(PoseWriter)
    WriterRegistry._default_writers.append(
        "PoseWriter"
    ) if "PoseWriter" not in WriterRegistry._default_writers else None

    # PytorchWriter
    WriterRegistry.register(PytorchWriter)
    WriterRegistry._default_writers.append(
        "PytorchWriter"
    ) if "PytorchWriter" not in WriterRegistry._default_writers else None

    # YCBVideoWriter
    WriterRegistry.register(YCBVideoWriter)
    WriterRegistry._default_writers.append(
        "YCBVideoWriter"
    ) if "YCBVideoWriter" not in WriterRegistry._default_writers else None
