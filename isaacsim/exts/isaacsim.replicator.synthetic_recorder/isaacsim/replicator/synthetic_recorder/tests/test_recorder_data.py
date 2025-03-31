# Copyright (c) 2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#


import os
import shutil
from collections import Counter

import omni.kit.app
import omni.kit.test
import omni.replicator.core as rep
import omni.timeline
import omni.usd
from isaacsim.replicator.synthetic_recorder.synthetic_recorder import SyntheticRecorder


# Check the contents of a folder against expected extension counts e.g expected_counts={png: 3, json: 3, npy: 3}
def validate_folder_contents(path: str, expected_counts: dict[str, int]) -> bool:
    if not os.path.exists(path) or not os.path.isdir(path):
        return False
    # Count the number of files with each extension and check that the counts match the expected counts
    file_counts = Counter(f.split(".")[-1] for f in os.listdir(path) if "." in f)
    return all(file_counts.get(ext, 0) == count for ext, count in expected_counts.items())


class TestRecorderData(omni.kit.test.AsyncTestCase):
    """
    Test that the recorder writes the correct number of frames
    """

    async def setUp(self):
        await omni.usd.get_context().new_stage_async()
        rep.create.cube(semantics=[("class", "cube")])
        rep.create.sphere(position=(1, 1, 0), semantics=[("class", "sphere")])

    async def tearDown(self):
        await omni.usd.get_context().new_stage_async()

    async def run_recorder_capture(self, num_frames, play_timeline, control_timeline):
        test_name = f"_out_num_frames_{num_frames}_play_timeline_{play_timeline}_control_timeline_{control_timeline}"
        print(f"Starting test: {test_name}")

        recorder = SyntheticRecorder()
        recorder.rt_subframes = 0
        recorder.verbose = True
        recorder.writer_name = "BasicWriter"
        recorder.basic_writer_params = {
            "rgb": True,
            "bounding_box_2d_tight": False,
            "bounding_box_2d_loose": False,
            "semantic_segmentation": False,
            "colorize_semantic_segmentation": False,
            "instance_id_segmentation": False,
            "colorize_instance_id_segmentation": False,
            "instance_segmentation": False,
            "colorize_instance_segmentation": False,
            "distance_to_camera": False,
            "distance_to_image_plane": False,
            "bounding_box_3d": False,
            "occlusion": False,
            "normals": False,
            "motion_vectors": False,
            "camera_params": False,
            "pointcloud": False,
            "pointcloud_include_unlabelled": False,
            "skeleton_data": False,
        }
        recorder.rp_data = [["/OmniverseKit_Persp", 512, 512, ""]]

        # Test parameters
        recorder.num_frames = num_frames
        recorder.control_timeline = control_timeline

        # Location to save the recording folder
        recorder.out_working_dir = os.getcwd()
        recorder.out_dir = test_name
        out_dir_path = os.path.join(recorder.out_working_dir, recorder.out_dir)

        # Clear the files in the output directory, keep the directory
        if os.path.exists(out_dir_path):
            shutil.rmtree(out_dir_path)

        # Check id the recorder should capture with the timeline running
        timeline = omni.timeline.get_timeline_interface()
        if play_timeline:
            timeline.play()
            await omni.kit.app.get_app().next_update_async()
        print(f"Timeline is_playing: {timeline.is_playing()}; current_time: {timeline.get_current_time()}")

        # Check if the timeline is in the correct state
        self.assertTrue(
            timeline.is_playing() == play_timeline,
            f"Timeline is not in the correct play state. Expected: {play_timeline}, Actual: {timeline.is_playing()}",
        )

        # Start the recorder and wait for all the data to be captured
        await recorder.start_stop_async()
        await omni.kit.app.get_app().next_update_async()
        print(f"Timeline is_playing: {timeline.is_playing()}; current_time: {timeline.get_current_time()}")

        # Check if the output directory was created
        self.assertTrue(os.path.exists(out_dir_path), f"Output directory {out_dir_path} was not created.")

        # If control_timeline is True, the timeline should not be playing after recording.
        if control_timeline:
            self.assertTrue(
                not timeline.is_playing(),
                "Timeline is still playing after recording when control_timeline is True.",
            )

        # If control_timeline is False and play_timeline is True, the timeline should still be playing.
        if not control_timeline and play_timeline:
            self.assertTrue(
                timeline.is_playing(),
                "Timeline is not playing after recording when control_timeline is False and play_timeline is True.",
            )

        # If not control_timeline and play_timeline is True, the timeline should be advanced.
        if not control_timeline and play_timeline:
            self.assertTrue(
                timeline.get_current_time() > 0.0,
                "Timeline did not advance after recording when control_timeline or play_timeline is True.",
            )

        # Check if the output directory contains the correct number of written frames
        self.assertTrue(
            validate_folder_contents(out_dir_path, {"png": num_frames}),
            f"Expected {num_frames} frames in {out_dir_path}, but found: {os.listdir(out_dir_path)}",
        )

    async def test_recorder_data_play_timeline_false_control_timeline_false(self):
        await self.run_recorder_capture(num_frames=10, play_timeline=False, control_timeline=False)

    async def test_recorder_data_play_timeline_false_control_timeline_true(self):
        await self.run_recorder_capture(num_frames=10, play_timeline=False, control_timeline=True)

    # ISIM-2602 - orchestrator.preview call causes an extra frame to be written if not called from UI
    # async def test_recorder_data_play_timeline_true_control_timeline_false(self):
    #     await self.run_recorder_capture(num_frames=10, play_timeline=True, control_timeline=False)

    # async def test_recorder_data_play_timeline_true_control_timeline_true(self):
    #     await self.run_recorder_capture(num_frames=10, play_timeline=True, control_timeline=True)
