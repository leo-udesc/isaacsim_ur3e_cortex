# Copyright (c) 2024, NVIDIA CORPORATION.  All rights reserved.

# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import carb
from isaacsim.replicator.behavior.base_behavior import BaseBehavior
from pxr import Sdf, Usd


class ExampleBaseBehavior(BaseBehavior):
    """
    Example randomizer that inherits from `BaseBehavior`.
    It exposes an additional attribute to include the children of the prim in the randomization.
    """

    BEHAVIOR_NS = "exampleBaseBehavior"
    VARIABLES_TO_EXPOSE = BaseBehavior.VARIABLES_TO_EXPOSE + [
        {
            "attr_name": "includeChildren",
            "attr_type": Sdf.ValueTypeNames.Bool,
            "default_value": True,
            "doc": "Include valid prim children to the behavior.",
        },
    ]

    def on_init(self):
        # Call the base class to setup the exposed attributes
        super().on_init()

        # List of the valid prims that to apply the behavior to
        self._valid_prims = []

    def on_destroy(self):
        """Called when the script is unassigned from a prim."""
        self._reset()
        super().on_destroy()

    def on_play(self):
        """Called when `play` is pressed."""
        super().on_play()
        self._setup()

    def on_stop(self):
        """Called when `stop` is pressed."""
        super().on_stop()
        self._reset()

    def _reset(self):
        """Reset the randomization."""
        # Set prims back to their initial state
        self._valid_prims = []

    def _setup(self):
        """Setup the randomizer."""
        # Read the exposed attribute values
        include_children = self._get_exposed_variable("includeChildren")

        # Get the valid prims to randomize
        if include_children:
            self._valid_prims = [prim for prim in Usd.PrimRange(self.prim) if prim.IsValid()]
        elif self.prim.IsValid():
            self._valid_prims = [self.prim]
        else:
            self._valid_prims = []
            carb.log_warn(f"[{self.prim_path}] No valid prims found to randomize.")
            return

    def _apply_behavior(self):
        # Apply the behavior for each prim
        for prim in self._valid_prims:
            print(f"[ExampleBaseBehavior][{self.prim_path}] Applying behavior to prim {prim.GetPath()}")
