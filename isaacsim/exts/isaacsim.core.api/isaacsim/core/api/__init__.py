# Copyright (c) 2021-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import builtins

from isaacsim.core.api.physics_context.physics_context import PhysicsContext
from isaacsim.core.api.simulation_context.simulation_context import SimulationContext
from isaacsim.core.api.world.world import World

# In case we are running from a regular kit instance and not a simulation_app, this variable is not defined.
if not hasattr(builtins, "ISAAC_LAUNCHED_FROM_TERMINAL"):
    builtins.ISAAC_LAUNCHED_FROM_TERMINAL = True
