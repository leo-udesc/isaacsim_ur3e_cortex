# Copyright (c) 2024, NVIDIA CORPORATION.  All rights reserved.

# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import asyncio

import carb
import omni.kit.window.property
from isaacsim.replicator.behavior.global_variables import EXPOSED_ATTR_NS
from isaacsim.replicator.behavior.utils.behavior_utils import (
    check_if_exposed_variables_should_be_removed,
    create_exposed_variables,
    get_exposed_variable,
    remove_exposed_variables,
)
from isaacsim.replicator.behavior.utils.scene_utils import (
    calculate_look_at_rotation,
    get_rotation_op_and_value,
    get_world_location,
    set_rotation_op_and_value,
    set_rotation_with_ops,
)
from omni.kit.scripting import BehaviorScript
from pxr import Gf, Sdf, Usd, UsdGeom


class LookAtBehavior(BehaviorScript):
    """
    Behavior script that orients prims to look at a target location or prim.
    The behavior can be applied to multiple prims at once, and the target can be a location or a prim.
    The behavior can be updated every frame or at a specified interval.
    """

    BEHAVIOR_NS = "lookAtBehavior"

    VARIABLES_TO_EXPOSE = [
        {
            "attr_name": "targetLocation",
            "attr_type": Sdf.ValueTypeNames.Vector3d,
            "default_value": Gf.Vec3d(0.0, 0.0, 0.0),
            "doc": "The 3D vector specifying the location to look at.",
        },
        {
            "attr_name": "targetPrimPath",
            "attr_type": Sdf.ValueTypeNames.String,
            "default_value": "",
            "doc": "The path of the target prim to look at. If specified, it has priority over the target location.",
        },
        {
            "attr_name": "upAxis",
            "attr_type": Sdf.ValueTypeNames.Vector3d,
            "default_value": Gf.Vec3d(0.0, 0.0, 1.0),
            "doc": (
                "The look-at up axis. Use the world up axis (e.g., Gf.Vec3d(0.0, 0.0, 1.0) for +Z) to keep\n"
                "the prim (usually camera) aligned with the world's vertical (e.g., to keep the horizon level).\n"
                "Or use the camera's local up axis (e.g., Gf.Vec3d(0.0, 1.0, 0.0) for +Y) if the camera moves."
            ),
        },
        {
            "attr_name": "includeChildren",
            "attr_type": Sdf.ValueTypeNames.Bool,
            "default_value": True,
            "doc": "Include prim children in the look-at randomization.",
        },
        {
            "attr_name": "interval",
            "attr_type": Sdf.ValueTypeNames.UInt,
            "default_value": 0,
            "doc": "Interval for updating the behavior. Value 0 means every frame.",
        },
    ]

    def on_init(self):
        """Called when the script is assigned to a prim."""
        self._target_location = Gf.Vec3d(0.0, 0.0, 0.0)
        self._target_prim = None
        self._up_axis = Gf.Vec3d(0.0, 0.0, 1.0)
        self._update_counter = 0
        self._interval = 0
        self._valid_prims = []
        self._initial_rotations = {}

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
        self._target_location = self._get_exposed_variable("targetLocation")
        target_prim_path = self._get_exposed_variable("targetPrimPath")
        self._include_children = self._get_exposed_variable("includeChildren")
        self._interval = self._get_exposed_variable("interval")
        self._up_axis = self._get_exposed_variable("upAxis")

        # Get the prims to apply the behavior to
        if self._include_children:
            self._valid_prims = [prim for prim in Usd.PrimRange(self.prim) if prim.IsA(UsdGeom.Xformable)]
        elif self.prim.IsA(UsdGeom.Xformable):
            self._valid_prims = [self.prim]
        else:
            self._valid_prims = []
            carb.log_warn(f"[{self.prim_path}] No valid prims found.")

        # Save the initial rotation op and value of the prims (create xformOp:orient if none present)
        for prim in self._valid_prims:
            rotation_data = get_rotation_op_and_value(prim)
            self._initial_rotations[prim] = rotation_data

        # Check if targetPrimPath is specified and retrieve the target prim
        if target_prim_path:
            self._target_prim = self.stage.GetPrimAtPath(target_prim_path)
            if not self._target_prim or not self._target_prim.IsValid() or not self._target_prim.IsA(UsdGeom.Xformable):
                self._target_prim = None
                carb.log_warn(f"[{self.prim_path}] Invalid target prim path: {target_prim_path}")

    def _reset(self):
        # Set prims back to their initial rotations
        for prim, rotation_data in self._initial_rotations.items():
            rotation_op_name, rotation_value = rotation_data
            set_rotation_op_and_value(prim, rotation_op_name, rotation_value)
        # Clear cached values
        self._valid_prims.clear()
        self._initial_rotations.clear()
        self._interval = 0
        self._update_counter = 0

    def _apply_behavior(self):
        target_location = self._get_target_location()

        for prim in self._valid_prims:
            # Get the world position of the current prim (camera) we want to orient towards the target
            eye = get_world_location(prim)

            # Calculate the look-at rotation
            look_at_rotation = calculate_look_at_rotation(eye, target_location, self._up_axis)

            # Set the rotation using and existing xformOp (orient, rotate, transform) or create a new default xformOp:orient
            set_rotation_with_ops(prim, look_at_rotation)

    def _get_target_location(self):
        # Fetches the target location from the prim or stored location
        if self._target_prim:
            return get_world_location(self._target_prim)
        return self._target_location

    def _get_exposed_variable(self, attr_name):
        full_attr_name = f"{EXPOSED_ATTR_NS}:{self.BEHAVIOR_NS}:{attr_name}"
        return get_exposed_variable(self.prim, full_attr_name)
