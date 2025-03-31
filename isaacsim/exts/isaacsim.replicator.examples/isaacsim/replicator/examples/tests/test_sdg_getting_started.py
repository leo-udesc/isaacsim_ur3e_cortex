# Copyright (c) 2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import os
import random
from collections import Counter

import omni.kit
import omni.replicator.core as rep
import omni.timeline
import omni.usd
from isaacsim.core.utils.semantics import add_update_semantics
from omni.replicator.core import Writer
from pxr import Sdf, UsdGeom, UsdPhysics


# Check the contents of a folder against expected extension counts e.g expected_counts={png: 3, json: 3, npy: 3}
def validate_folder_contents(path: str, expected_counts: dict[str, int]) -> bool:
    if not os.path.exists(path) or not os.path.isdir(path):
        return False

    # Count the number of files with each extension
    file_counts = Counter(f.split(".")[-1] for f in os.listdir(path) if "." in f)
    print(f"File counts: {file_counts}")

    # Check that the counts match the expected counts
    return all(file_counts.get(ext, 0) == count for ext, count in expected_counts.items())


class TestSDGGettingStarted(omni.kit.test.AsyncTestCase):
    async def setUp(self):
        await omni.kit.app.get_app().next_update_async()
        omni.usd.get_context().new_stage()
        await omni.kit.app.get_app().next_update_async()

    async def tearDown(self):
        await omni.kit.app.get_app().next_update_async()
        omni.usd.get_context().new_stage()
        await omni.kit.app.get_app().next_update_async()

    async def test_sdg_getting_started_01(self):
        # Create a new stage and disable capture on play
        omni.usd.get_context().new_stage()
        rep.orchestrator.set_capture_on_play(False)

        # Setup the stage with a dome light and a cube
        stage = omni.usd.get_context().get_stage()
        dome_light = stage.DefinePrim("/World/DomeLight", "DomeLight")
        dome_light.CreateAttribute("inputs:intensity", Sdf.ValueTypeNames.Float).Set(500.0)
        cube = stage.DefinePrim("/World/Cube", "Cube")
        add_update_semantics(cube, "MyCube")

        # Create a render product using the viewport perspective camera
        rp = rep.create.render_product("/OmniverseKit_Persp", (512, 512))

        # Write data using the basic writer with the rgb and bounding box annotators
        writer = rep.writers.get("BasicWriter")
        out_dir = os.getcwd() + "/_out_basic_writer"
        print(f"Output directory: {out_dir}")
        writer.initialize(output_dir=out_dir, rgb=True, bounding_box_2d_tight=True)
        writer.attach(rp)

        # Trigger a data capture request (data will be written to disk by the writer)
        for i in range(3):
            print(f"Step {i}")
            await rep.orchestrator.step_async()

        # Destroy the render product to release resources by detaching it from the writer first
        writer.detach()
        rp.destroy()

        # Wait for the data to be written to disk
        await rep.orchestrator.wait_until_complete_async()

        # Validate the output directory contents
        self.assertTrue(validate_folder_contents(path=out_dir, expected_counts={"png": 3, "json": 6, "npy": 3}))

    async def test_sdg_getting_started_02(self):
        class MyWriter(Writer):
            def __init__(self, camera_params: bool = True, bounding_box_3d: bool = True):
                # Organize data from render product perspective (legacy, annotator, renderProduct)
                self.data_structure = "renderProduct"
                if camera_params:
                    self.annotators.append(rep.annotators.get("camera_params"))
                if bounding_box_3d:
                    self.annotators.append(rep.annotators.get("bounding_box_3d"))
                self._frame_id = 0

            def write(self, data):
                print(f"[MyWriter][{self._frame_id}] data:{data}")
                self._frame_id += 1

        # Register the writer for use
        rep.writers.register_writer(MyWriter)

        # Create a new stage and disable capture on play
        omni.usd.get_context().new_stage()
        rep.orchestrator.set_capture_on_play(False)

        # Setup stage
        stage = omni.usd.get_context().get_stage()
        dome_light = stage.DefinePrim("/World/DomeLight", "DomeLight")
        dome_light.CreateAttribute("inputs:intensity", Sdf.ValueTypeNames.Float).Set(500.0)
        cube = stage.DefinePrim("/World/Cube", "Cube")
        add_update_semantics(cube, "MyCube")

        # Capture from two perspectives, a custom camera and the viewport perspective camera
        camera = stage.DefinePrim("/World/Camera", "Camera")
        UsdGeom.Xformable(camera).AddTranslateOp().Set((0, 0, 20))

        # Create the render products
        rp_cam = rep.create.render_product(camera.GetPath(), (400, 400), name="camera_view")
        rp_persp = rep.create.render_product("/OmniverseKit_Persp", (512, 512), name="perspective_view")

        # Use the annotators to access the data directly, each annotator is attached to a render product
        rgb_annotator_cam = rep.annotators.get("rgb")
        rgb_annotator_cam.attach(rp_cam)
        rgb_annotator_persp = rep.annotators.get("rgb")
        rgb_annotator_persp.attach(rp_persp)

        # Use the custom writer to access the annotator data
        custom_writer = rep.writers.get("MyWriter")
        custom_writer.initialize(camera_params=True, bounding_box_3d=True)
        custom_writer.attach([rp_cam, rp_persp])

        # Use the pose writer to write the data to disk
        pose_writer = rep.WriterRegistry.get("PoseWriter")
        out_dir = os.getcwd() + "/_out_pose_writer"
        print(f"Output directory: {out_dir}")
        pose_writer.initialize(output_dir=out_dir, write_debug_images=True)
        pose_writer.attach([rp_cam, rp_persp])

        # Trigger a data capture request (data will be written to disk by the writer)
        for i in range(3):
            print(f"Step {i}")
            await rep.orchestrator.step_async()

            # Get the data from the annotators
            rgb_data_cam = rgb_annotator_cam.get_data()
            rgb_data_persp = rgb_annotator_persp.get_data()
            print(f"[Annotator][Cam][{i}] rgb_data_cam shape: {rgb_data_cam.shape}")
            print(f"[Annotator][Persp][{i}] rgb_data_persp shape: {rgb_data_persp.shape}")

        # Detach the render products from the annotators and writers and clear them to release resources
        pose_writer.detach()
        custom_writer.detach()
        rgb_annotator_cam.detach()
        rgb_annotator_persp.detach()
        rp_cam.destroy()
        rp_persp.destroy()

        # Wait for the data to be written to disk
        await rep.orchestrator.wait_until_complete_async()

        # Validate the output directory contents
        self.assertTrue(validate_folder_contents(path=out_dir, expected_counts={"png": 12, "json": 6}))

    async def test_sdg_getting_started_03(self):
        # Custom randomizer function using USD API
        def randomize_location(prim):
            if not prim.GetAttribute("xformOp:translate"):
                UsdGeom.Xformable(prim).AddTranslateOp()
            translate = prim.GetAttribute("xformOp:translate")
            translate.Set((random.uniform(-2, 2), random.uniform(-2, 2), random.uniform(-2, 2)))

        # Create a new stage and disable capture on play
        omni.usd.get_context().new_stage()
        rep.orchestrator.set_capture_on_play(False)
        random.seed(42)
        rep.set_global_seed(42)

        # Setup stage
        stage = omni.usd.get_context().get_stage()
        cube = stage.DefinePrim("/World/Cube", "Cube")
        add_update_semantics(cube, "MyCube")

        # Create a replicator randomizer with custom event trigger
        with rep.trigger.on_custom_event(event_name="randomize_dome_light_color"):
            rep.create.light(light_type="Dome", color=rep.distribution.uniform((0, 0, 0), (1, 1, 1)))

        # Create a render product using the viewport perspective camera
        rp = rep.create.render_product("/OmniverseKit_Persp", (512, 512))

        # Write data using the basic writer with the rgb and bounding box annotators
        writer = rep.writers.get("BasicWriter")
        out_dir = os.getcwd() + "/_out_basic_writer_rand"
        print(f"Output directory: {out_dir}")
        writer.initialize(output_dir=out_dir, rgb=True, semantic_segmentation=True, colorize_semantic_segmentation=True)
        writer.attach(rp)

        # Trigger a data capture request (data will be written to disk by the writer)
        for i in range(3):
            print(f"Step {i}")
            # Trigger the custom event randomizer every other step
            if i % 2 == 1:
                rep.utils.send_og_event(event_name="randomize_dome_light_color")

            # Run the custom USD API location randomizer on the prims
            randomize_location(cube)

            # Since the replicator randomizer is set to trigger on custom events, step will only trigger the writer
            await rep.orchestrator.step_async()

        # Destroy the render product to release resources by detaching it from the writer first
        writer.detach()
        rp.destroy()

        # Wait for the data to be written to disk
        await rep.orchestrator.wait_until_complete_async()

        # Validate the output directory contents
        self.assertTrue(validate_folder_contents(path=out_dir, expected_counts={"png": 6, "json": 3}))

    async def test_sdg_getting_started_04(self):
        def add_colliders_and_rigid_body_dynamics(prim):
            # Add colliders
            if not prim.HasAPI(UsdPhysics.CollisionAPI):
                collision_api = UsdPhysics.CollisionAPI.Apply(prim)
            else:
                collision_api = UsdPhysics.CollisionAPI(prim)
            collision_api.CreateCollisionEnabledAttr(True)
            # Add rigid body dynamics
            if not prim.HasAPI(UsdPhysics.RigidBodyAPI):
                rigid_body_api = UsdPhysics.RigidBodyAPI.Apply(prim)
            else:
                rigid_body_api = UsdPhysics.RigidBodyAPI(prim)
            rigid_body_api.CreateRigidBodyEnabledAttr(True)

        # Create a new stage and disable capture on play
        omni.usd.get_context().new_stage()
        rep.orchestrator.set_capture_on_play(False)

        # Add a light
        stage = omni.usd.get_context().get_stage()
        dome_light = stage.DefinePrim("/World/DomeLight", "DomeLight")
        dome_light.CreateAttribute("inputs:intensity", Sdf.ValueTypeNames.Float).Set(500.0)

        # Create a cube with colliders and rigid body dynamics at a specific location
        cube = stage.DefinePrim("/World/Cube", "Cube")
        add_colliders_and_rigid_body_dynamics(cube)
        if not cube.GetAttribute("xformOp:translate"):
            UsdGeom.Xformable(cube).AddTranslateOp()
        cube.GetAttribute("xformOp:translate").Set((0, 0, 2))
        add_update_semantics(cube, "MyCube")

        # Createa a sphere with colliders and rigid body dynamics next to the cube
        sphere = stage.DefinePrim("/World/Sphere", "Sphere")
        add_colliders_and_rigid_body_dynamics(sphere)
        if not sphere.GetAttribute("xformOp:translate"):
            UsdGeom.Xformable(sphere).AddTranslateOp()
        sphere.GetAttribute("xformOp:translate").Set((-1, -1, 2))
        add_update_semantics(sphere, "MySphere")

        # Create a render product using the viewport perspective camera
        rp = rep.create.render_product("/OmniverseKit_Persp", (512, 512))

        # Write data using the basic writer with the rgb and bounding box annotators
        writer = rep.writers.get("BasicWriter")
        out_dir = os.getcwd() + "/_out_basic_writer_sim"
        print(f"Output directory: {out_dir}")
        writer.initialize(output_dir=out_dir, rgb=True, semantic_segmentation=True, colorize_semantic_segmentation=True)
        writer.attach(rp)

        # Start the timeline (will only advance with app update)
        timeline = omni.timeline.get_timeline_interface()
        timeline.play()

        # Update the app and implicitly advance the simulation
        drop_delta = 0.5
        last_capture_height = cube.GetAttribute("xformOp:translate").Get()[2]
        for i in range(100):
            # Get the current height of the cube and the distance it dropped since the last capture
            await omni.kit.app.get_app().next_update_async()
            current_height = cube.GetAttribute("xformOp:translate").Get()[2]
            drop_since_last_capture = last_capture_height - current_height
            print(
                f"Step {i}; cube height: {current_height:.3f}; drop since last capture: {drop_since_last_capture:.3f}"
            )

            # Stop the simulation if the cube falls below the ground
            if current_height < 0:
                print(f"\t Cube fell below the ground at height {current_height:.3f}, stopping simulation..")
                timeline.pause()
                break

            # Capture every time the cube drops by the threshold distance
            if drop_since_last_capture >= drop_delta:
                print(f"\t Capturing at height {current_height:.3f}")
                last_capture_height = current_height
                # Pause the timeline to capture multiple frames of the same simulation state
                timeline.pause()

                # Setting delta_time to 0.0 will make sure the step function will not advance the simulation during capture
                await rep.orchestrator.step_async(delta_time=0.0)

                # Capture again with the cube hidden
                UsdGeom.Imageable(cube).MakeInvisible()
                await rep.orchestrator.step_async(delta_time=0.0)
                UsdGeom.Imageable(cube).MakeVisible()

                # Resume the timeline to continue the simulation
                timeline.play()

        # Destroy the render product to release resources by detaching it from the writer first
        writer.detach()
        rp.destroy()

        # Wait for the data to be written to disk
        await rep.orchestrator.wait_until_complete_async()

        # Validate the output directory contents
        self.assertTrue(validate_folder_contents(path=out_dir, expected_counts={"png": 12, "json": 6}))
