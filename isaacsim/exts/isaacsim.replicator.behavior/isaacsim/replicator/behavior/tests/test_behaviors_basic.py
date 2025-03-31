# Copyright (c) 2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import importlib
import os

import isaacsim.replicator.behavior.behaviors as behaviors_module
import omni.kit.app
import omni.kit.commands
import omni.kit.test
import omni.timeline
import omni.usd
from isaacsim.replicator.behavior.global_variables import EXPOSED_ATTR_NS
from omni.kit.scripting import BehaviorScript
from pxr import Sdf

SCRIPTS_ATTR = "omni:scripting:scripts"

# Get the behavior classes to test from the behaviors module __all__ list
BEHAVIOR_CLASSES = [getattr(behaviors_module, class_name) for class_name in behaviors_module.__all__]
print(f"BEHAVIOR_CLASSES: {BEHAVIOR_CLASSES}")


class TestBehaviorsBasic(omni.kit.test.AsyncTestCase):
    """
    Test the basic functionality of the behavior scripts.
    """

    async def setup(self):
        pass

    async def tearDown(self):
        pass

    async def check_exposed_variables(self, behavior_class):
        # Make sure behavior_class is of type BehaviorScript
        self.assertTrue(
            issubclass(behavior_class, BehaviorScript),
            f"Behavior class '{behavior_class.__name__}' is not a subclass of BehaviorScript",
        )

        # Create a fresh stage with a root prim and some child prims
        await omni.usd.get_context().new_stage_async()
        stage = omni.usd.get_context().get_stage()
        root_prim_path = "/World/RootPrim"
        root_prim = stage.DefinePrim(root_prim_path, "Xform")

        # Add scripting API to the prim
        omni.kit.commands.execute("ApplyScriptingAPICommand", paths=[root_prim_path])
        await omni.kit.app.get_app().next_update_async()
        scripts_attr = root_prim.GetAttribute(SCRIPTS_ATTR)
        self.assertTrue(
            scripts_attr and scripts_attr.IsValid(), f"No '{SCRIPTS_ATTR}' attribute found on prim: {root_prim_path}"
        )

        # Get the script path from the behavior class's module
        module = importlib.import_module(behavior_class.__module__)
        script_full_path = module.__file__

        self.assertTrue(os.path.exists(script_full_path), f"Script path does not exist: {script_full_path}")
        self.assertTrue(script_full_path.endswith(".py"), f"Script path is not a .py file: {script_full_path}")

        # Add the behavior script path the list of scripts on the prim
        current_scripts = scripts_attr.Get()
        if current_scripts is None:
            current_scripts = []
        current_scripts.append(Sdf.AssetPath(script_full_path))
        scripts_attr.Set(current_scripts)

        # NOTE, at least 3 updates are needed to ensure the script is loaded and the exposed vars are set
        for _ in range(3):
            await omni.kit.app.get_app().next_update_async()

        # Check if the class has VARIABLES_TO_EXPOSE
        self.assertTrue(
            hasattr(behavior_class, "VARIABLES_TO_EXPOSE"),
            f"Behavior class '{behavior_class.__name__}' does not have a 'VARIABLES_TO_EXPOSE' attribute",
        )

        # Check if the class has a BEHAVIOR_NS attribute
        self.assertTrue(
            hasattr(behavior_class, "BEHAVIOR_NS"),
            f"Behavior class '{behavior_class.__name__}' does not have a 'BEHAVIOR_NS' attribute",
        )
        # Full namespace for the exposed variables
        full_ns = f"{EXPOSED_ATTR_NS}:{behavior_class.BEHAVIOR_NS}"

        # Iterate over the variables which should be exposed with the behavior script initialization
        for exposed_var in behavior_class.VARIABLES_TO_EXPOSE:
            # Check if the exposed variable is set on the prim
            attr_name = exposed_var["attr_name"]
            print(f"\tChecking exposed variable: {attr_name}")
            attr_full_name = f"{full_ns}:{attr_name}"
            attribute = root_prim.GetAttribute(attr_full_name)
            self.assertTrue(
                attribute and attribute.IsValid(), f"Attribute '{attr_full_name}' not found on prim: {root_prim_path}"
            )

            # Check if the exposed variable has the correct type
            attr_type = exposed_var["attr_type"]
            self.assertEqual(
                attribute.GetTypeName(),
                attr_type,
                f"Attribute '{attr_full_name}' has incorrect type: {attribute.GetTypeName()} instead of {attr_type}",
            )

            # Check if the exposed variable has a default value
            # NOTE: only checking if there is a default value, not the actual value due to rounding issues
            self.assertTrue(
                attribute.Get() is not None,
                f"Attribute '{attr_full_name}' does not have a valid value: {attribute.Get()} ",
            )

            # Check if the exposed variable has the correct documentation
            doc = exposed_var.get("doc", "")
            self.assertEqual(
                attribute.GetDocumentation(),
                doc,
                f"Attribute '{attr_full_name}' has incorrect documentation: {attribute.GetDocumentation()} instead of {doc}",
            )

        # Basic test to check if the behavior can run for a few frames
        timeline = omni.timeline.get_timeline_interface()
        print(f"\tStarting timeline for several frames")
        timeline.play()
        for _ in range(10):
            await omni.kit.app.get_app().next_update_async()
        print(f"\tPausing timeline")
        timeline.pause()
        await omni.kit.app.get_app().next_update_async()
        print(f"\tStopping timeline")
        timeline.stop()
        await omni.kit.app.get_app().next_update_async()

        # Remove the behavior script from the prim, this should also remove/invalidate the attributes of the exposed variables
        print(f"\tChecking if exposed variables are removed after clearing the scripts attribute")
        scripts_attr.Set([])

        # NOTE, at least 3 updates are needed to ensure the script is loaded and the exposed vars are set
        for _ in range(3):
            await omni.kit.app.get_app().next_update_async()

        # Check if the exposed variables are removed
        for exposed_var in behavior_class.VARIABLES_TO_EXPOSE:
            attr_name = exposed_var["attr_name"]
            attr_full_name = f"{full_ns}:{attr_name}"
            attribute = root_prim.GetAttribute(attr_full_name)
            self.assertFalse(
                attribute and attribute.IsValid(),
                f"Attribute '{attr_full_name}' with {attribute.Get()} not removed from prim: {root_prim_path}",
            )

    async def test_exposed_variables(self):
        for behavior_class in BEHAVIOR_CLASSES:
            print(f"Testing behavior: {behavior_class.__name__}")
            await self.check_exposed_variables(behavior_class)
