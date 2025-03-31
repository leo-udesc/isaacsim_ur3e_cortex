# Copyright (c) 2024, NVIDIA CORPORATION.  All rights reserved.

# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import random

import carb
import omni.kit.commands
import omni.kit.window.property
import omni.usd
from isaacsim.replicator.behavior.global_variables import EXPOSED_ATTR_NS
from isaacsim.replicator.behavior.utils.behavior_utils import (
    check_if_exposed_variables_should_be_removed,
    create_exposed_variables,
    get_exposed_variable,
    remove_exposed_variables,
)
from omni.kit.scripting import BehaviorScript
from pxr import Gf, Sdf, Usd, UsdLux


class LightRandomizer(BehaviorScript):
    """
    Behavior script that randomizes light properties such as intensity and color for light prim(s).
    """

    BEHAVIOR_NS = "lightRandomizer"
    VARIABLES_TO_EXPOSE = [
        {
            "attr_name": "includeChildren",
            "attr_type": Sdf.ValueTypeNames.Bool,
            "default_value": True,
            "doc": "Include valid prim children to the behavior.",
        },
        {
            "attr_name": "interval",
            "attr_type": Sdf.ValueTypeNames.UInt,
            "default_value": 0,
            "doc": "Interval for updating the behavior. Value 0 means every frame.",
        },
        {
            "attr_name": "range:minColor",
            "attr_type": Sdf.ValueTypeNames.Color3f,
            "default_value": Gf.Vec3f(0.1, 0.1, 0.1),
            "doc": "Minimum RGB values for the light color randomization.",
        },
        {
            "attr_name": "range:maxColor",
            "attr_type": Sdf.ValueTypeNames.Color3f,
            "default_value": Gf.Vec3f(0.9, 0.9, 0.9),
            "doc": "Maximum RGB values for the light color randomization.",
        },
        {
            "attr_name": "range:intensity",
            "attr_type": Sdf.ValueTypeNames.Float2,
            "default_value": Gf.Vec2f(1000.0, 20000.0),
            "doc": "Range for the light intensity as (min, max).",
        },
    ]

    def on_init(self):
        """Called when the script is assigned to a prim."""
        self._update_counter = 0
        self._interval = 0
        self._valid_prims = []
        self._initial_attributes = {}

        # Expose the variables as USD attributes
        create_exposed_variables(self.prim, EXPOSED_ATTR_NS, self.BEHAVIOR_NS, self.VARIABLES_TO_EXPOSE)

        # Refresh the property windows to show the exposed variables
        omni.kit.window.property.get_window().request_rebuild()

    def on_destroy(self):
        """Called when the script is unassigned from a prim."""
        self._reset()
        # Exposed variables should be removed if the script is no longer assigned to the prim
        if check_if_exposed_variables_should_be_removed(self.prim, __file__):
            remove_exposed_variables(self.prim, EXPOSED_ATTR_NS, self.BEHAVIOR_NS, self.VARIABLES_TO_EXPOSE)
            omni.kit.window.property.get_window().request_rebuild()

    def on_play(self):
        """Called when `play` is pressed."""
        self._setup()
        # Make sure the initial behavior is applied if the interval is larger than 0
        if self._interval > 0:
            self._apply_behavior()

    def on_stop(self):
        """Called when `stop` is pressed."""
        self._reset()

    def on_update(self, current_time: float, delta_time: float):
        """Called on per frame update events that occur when `playing`."""
        if delta_time <= 0:
            return
        if self._interval <= 0:
            self._apply_behavior()
        else:
            self._update_counter += 1
            if self._update_counter >= self._interval:
                self._apply_behavior()
                self._update_counter = 0

    def _setup(self):
        # Fetch the exposed attributes
        include_children = self._get_exposed_variable("includeChildren")
        self._interval = self._get_exposed_variable("interval")
        self._min_color = self._get_exposed_variable("range:minColor")
        self._max_color = self._get_exposed_variable("range:maxColor")
        self._intensity_range = self._get_exposed_variable("range:intensity")

        # Get the valid prims (light prims)
        if include_children:
            self._valid_prims = [prim for prim in Usd.PrimRange(self.prim) if prim.HasAPI(UsdLux.LightAPI)]
        elif self.prim.HasAPI(UsdLux.LightAPI):
            self._valid_prims = [self.prim]
        else:
            self._valid_prims = []
            carb.log_warn(f"[{self.prim_path}] No valid light prims found.")

        # Cache original attributes to restore after randomization
        self._initial_attributes = {}
        for prim in self._valid_prims:
            self._cache_initial_attributes(prim)

    def _reset(self):
        # Restore original attributes
        for prim, attrs in self._initial_attributes.items():
            for attr_name, attr_value in attrs.items():
                prim.GetAttribute(attr_name).Set(attr_value)

        # Clear cached values
        self._valid_prims.clear()
        self._initial_attributes.clear()
        self._update_counter = 0

    def _apply_behavior(self):
        for prim in self._valid_prims:
            rand_color = (
                random.uniform(self._min_color[0], self._max_color[0]),
                random.uniform(self._min_color[1], self._max_color[1]),
                random.uniform(self._min_color[2], self._max_color[2]),
            )
            prim.GetAttribute("inputs:color").Set(rand_color)

            rand_intensity = random.uniform(self._intensity_range[0], self._intensity_range[1])
            prim.GetAttribute("inputs:intensity").Set(rand_intensity)

    def _cache_initial_attributes(self, prim):
        if not prim.HasAttribute("inputs:intensity"):
            prim.CreateAttribute("inputs:intensity", Sdf.ValueTypeNames.Float)
        if not prim.HasAttribute("inputs:color"):
            prim.CreateAttribute("inputs:color", Sdf.ValueTypeNames.Color3f)
        self._initial_attributes[prim] = {
            "inputs:intensity": prim.GetAttribute("inputs:intensity").Get(),
            "inputs:color": prim.GetAttribute("inputs:color").Get(),
        }

    def _get_exposed_variable(self, attr_name):
        full_attr_name = f"{EXPOSED_ATTR_NS}:{self.BEHAVIOR_NS}:{attr_name}"
        return get_exposed_variable(self.prim, full_attr_name)
