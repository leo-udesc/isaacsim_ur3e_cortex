# Copyright (c) 2024, NVIDIA CORPORATION.  All rights reserved.

# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import carb
import carb.events
import omni.kit.app
import omni.kit.commands
from pxr import Sdf, Usd


def create_exposed_variable(
    prim: Usd.Prim, full_attr_name: str, attr_type: Sdf.ValueTypeName, default_value, doc: str = None
) -> Usd.Attribute:
    """Creates a USD attribute on the prim to expose the variable to the UI, if the variable exits it returns it."""
    attr = prim.GetAttribute(full_attr_name)
    if attr:
        return attr
    attr = prim.CreateAttribute(full_attr_name, attr_type)
    attr.Set(default_value)
    if doc:
        attr.SetDocumentation(doc)
    return attr


def create_exposed_variables(prim: Usd.Prim, exposed_attr_ns: str, behavior_ns: str, variables_to_expose: dict) -> None:
    """Create exposed variables based on the provided namespaces and data dictionary"""
    # Check if there are any attributes to lock (e.g. constant placeholders -- cannot be edited in the UI)
    attr_to_lock = []
    for var in variables_to_expose:
        attr_name = var["attr_name"]
        full_attr_name = f"{exposed_attr_ns}:{behavior_ns}:{attr_name}"
        attr = create_exposed_variable(
            prim=prim,
            full_attr_name=full_attr_name,
            attr_type=var["attr_type"],
            default_value=var["default_value"],
            doc=var.get("doc"),
        )
        if var.get("lock"):
            attr_to_lock.append(attr.GetPath())
    import asyncio

    asyncio.ensure_future(lock_exposed_variables(attr_to_lock))


async def lock_exposed_variables(attr_paths):
    """Lock exposed variables to prevent editing in the UI."""
    await omni.kit.app.get_app().next_update_async()
    omni.kit.commands.execute("LockSpecsCommand", spec_paths=attr_paths)


def check_if_exposed_variables_should_be_removed(prim: Usd.Prim, script_file_path: str) -> bool:
    """Remove exposed variables if the script is no longer assigned to the prim."""
    if prim is None or not prim.IsValid():
        # Invalid prim, cannot remove variables
        return False

    scripts_attr = prim.GetAttribute("omni:scripting:scripts")
    if not scripts_attr:
        # No scripts attribute, remove variables
        return True

    scripts_paths: Sdf.AssetPathArray = scripts_attr.Get()
    if not scripts_paths:
        # Empty scripts attribute, remove variables
        return True

    # Remove variables if script is not in the attached scripts list (e.g. script was removed)
    return not any(script_file_path == asset.path for asset in scripts_paths)


def remove_exposed_variable(prim: Usd.Prim, full_attr_name: str, remove_from_fabric: bool = True) -> None:
    """Remove the exposed variable from the prim."""
    if prim is None or not prim.IsValid():
        carb.log_warn(f"Prim {prim.GetPath()} is not valid, cannot remove exposed variable {full_attr_name}")
        return
    attr = prim.GetAttribute(full_attr_name)
    if attr:
        prim.RemoveProperty(attr.GetName())
        # Remove the attribute from fabric as well
        if remove_from_fabric:
            import usdrt
            from pxr import UsdUtils

            stage = prim.GetStage()
            stage_id = UsdUtils.StageCache.Get().GetId(stage).ToLongInt()
            stage_rt = usdrt.Usd.Stage.Attach(stage_id)
            prim_rt = stage_rt.GetPrimAtPath(usdrt.Sdf.Path(prim.GetPath().pathString))
            attr_rt = prim_rt.GetAttribute(full_attr_name)
            if attr_rt:
                prim_rt.RemoveProperty(full_attr_name)
    else:
        carb.log_warn(f"Attribute {full_attr_name} not found on {prim.GetPath()}")


def remove_exposed_variables(prim: Usd.Prim, exposed_attr_ns: str, behavior_ns: str, variables_to_expose: dict) -> None:
    """Remove exposed variables based on the provided namespaces and data dictionary"""
    for var in variables_to_expose:
        attr_name = var["attr_name"]
        full_attr_name = f"{exposed_attr_ns}:{behavior_ns}:{attr_name}"
        remove_exposed_variable(prim, full_attr_name)


def get_exposed_variable(prim: Usd.Prim, full_attr_name: str):
    """Helper function to get the value of an exposed attribute."""
    if prim is None or not prim.IsValid():
        carb.log_warn(f"Prim is not valid, cannot receive exposed variable {full_attr_name}")
        return None
    attr = prim.GetAttribute(full_attr_name)
    if attr:
        return attr.Get()
    else:
        return None


def set_exposed_variables(prim: Usd.Prim, exposed_variables: dict) -> None:
    """Sets exposed variables based on the provided data dictionary"""
    if prim is None or not prim.IsValid():
        carb.log_warn(f"Prim is not valid, cannot receive exposed variable")
        return
    for attr_name, value in exposed_variables.items():
        attr = prim.GetAttribute(attr_name)
        if attr:
            attr.Set(value)
        else:
            print(f"Attribute {attr_name} not found on {prim.GetPath()}")


def remove_empty_scopes(prim: Usd.Prim, stage: Usd.Stage) -> None:
    """Recursively (post-order) remove Scope or GenericPrim prims with no valid children from stage."""
    if prim is None or not prim.IsValid():
        return

    for child in prim.GetChildren():
        remove_empty_scopes(child, stage)

    prim_type = prim.GetTypeName() or "GenericPrim"

    if prim_type in ("GenericPrim", "Scope"):
        if not any(child.IsValid() for child in prim.GetChildren()):
            stage.RemovePrim(prim.GetPath())


def add_behavior_script(prim: Usd.Prim, script_path: str, allow_duplicates: bool = False) -> None:
    """Adds a behavior script to the prim avoiding duplicates by default."""
    if prim is None or not prim.IsValid():
        carb.log_warn(f"Prim is not valid, cannot add behavior script.")
        return

    # Ensure the scripting API is applied to the prim
    scripts_attr = prim.GetAttribute("omni:scripting:scripts")
    if not scripts_attr:
        print(f"Applying scripting API to prim: {prim.GetPath()}")
        omni.kit.commands.execute("ApplyScriptingAPICommand", paths=[prim.GetPath()])
        scripts_attr = prim.GetAttribute("omni:scripting:scripts")
        if not scripts_attr:
            print(f"Failed to create scripting attribute on prim: {prim.GetPath()}, cannot add behavior script.")
            return

    # Convert paths from immutable AssetPathArray to list of strings
    current_scripts = [asset.path for asset in scripts_attr.Get() or []]
    if allow_duplicates or script_path not in current_scripts:
        current_scripts.append(script_path)
        scripts_attr.Set(Sdf.AssetPathArray(current_scripts))


async def add_behavior_script_with_parameters_async(
    prim: Usd.Prim, script_path: str, exposed_variables: dict = {}, allow_duplicates: bool = False
) -> None:
    """Add a behavior script to a prim and set its parameters."""
    if prim is None or not prim.IsValid():
        carb.log_warn(f"Prim is not valid, cannot add behavior script.")
        return

    # Add the behavior script to the prim
    add_behavior_script(prim, script_path, allow_duplicates=allow_duplicates)

    # Wait a few frames for the exposed variables to be available
    for _ in range(3):
        await omni.kit.app.get_app().next_update_async()

    # Set the behavior script parameters
    set_exposed_variables(prim, exposed_variables)


async def publish_event_and_wait_for_completion_async(
    publish_payload: dict,
    expected_payload: dict,
    publish_event_name: str,
    subscribe_event_name: str,
    max_wait_updates: int,
    verbose: bool = True,
) -> bool:
    """Publishes an event and waits for a response that matches the expected payload."""
    # Keep track of whether the action is complete
    is_action_complete = False

    # Callback to listen to incoming events
    def on_event_received(event: carb.events.IEvent) -> None:
        """Checks if the event payload matches the expected key-value pairs."""
        payload_dict = event.payload.get_dict()
        if all(item in payload_dict.items() for item in expected_payload.items()):
            if verbose:
                print(f"\tAction completed, received payload: {payload_dict}")
            nonlocal is_action_complete
            is_action_complete = True
        else:
            if verbose:
                print(f"\tAction not complete, received payload: {payload_dict}, continuing..")

    # Start listening to incoming events
    message_bus = omni.kit.app.get_app().get_message_bus_event_stream()
    sub_event_type = carb.events.type_from_string(subscribe_event_name)
    if verbose:
        print(f"Subscribing to {subscribe_event_name}")
    sub_pop = message_bus.create_subscription_to_pop_by_type(sub_event_type, on_event_received)

    try:
        # Publish the payload
        pub_event_type = carb.events.type_from_string(publish_event_name)
        if verbose:
            print(f"Publishing payload: {publish_payload}")
            print(f"Waiting for response: {expected_payload}")
        message_bus.push(pub_event_type, payload=publish_payload)

        # Wait for action completion
        for i in range(max_wait_updates):
            if is_action_complete:
                if verbose:
                    print(f"\t\tExpected payload received after {i} updates.")
                break
            await omni.kit.app.get_app().next_update_async()
        else:
            if verbose:
                print(f"\t\tTimeout after {max_wait_updates} updates.")
    finally:
        # Unsubscribe from events
        if verbose:
            print(f"Unsubscribing from {subscribe_event_name}")
        sub_pop.unsubscribe()

    return is_action_complete
