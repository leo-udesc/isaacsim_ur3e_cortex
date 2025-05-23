# Copyright (c) 2022-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import gc
import weakref
from functools import partial

import omni.ext
import omni.kit.commands
from omni.kit.menu.utils import MenuItemDescription, add_menu_items, remove_menu_items


class Extension(omni.ext.IExt):
    def on_startup(self, ext_id: str) -> None:

        action_registry = omni.kit.actions.core.get_action_registry()
        action_registry.register_action(
            ext_id,
            "isaac_create_surface_gripper",
            partial(self.menu_click),
            display_name="Create Surface Gripper",
            description="Create a physics based gripper for simulating suction/surface type grippers",
            tag="Create Surface Gripper",
        )
        menu_entry = [
            MenuItemDescription(
                name="Surface Gripper",
                # glyph="plug.svg",
                onclick_action=(ext_id, "isaac_create_surface_gripper"),
            )
        ]

        self._menu_items = [MenuItemDescription("Robotics", sub_menu=menu_entry)]
        add_menu_items(self._menu_items, "Tools")

    def on_shutdown(self):
        remove_menu_items(self._menu_items, "Tools")
        gc.collect()

    def menu_click(self):
        _, prim = omni.kit.commands.execute("CreateSurfaceGripper")
