# Copyright (c) 2023-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from __future__ import annotations

import time
from typing import List, Optional, Tuple

import carb
import omni.kit.test


def get_last_gpu_time_ms(
    hydra_engine_stats: HydraEngineStats,
) -> float:
    """
    Return the RTX Renderer duration (in milliseconds) as seen in the profiler window.
    """
    if hydra_engine_stats is None:
        return 0.0

    device_nodes = hydra_engine_stats.get_gpu_profiler_result()

    total_time = 0.0

    # jcannon TODO: make this handle multi GPU
    for node in device_nodes[0]:
        # RTX Renderer duration, seems to always be available even if the profiler
        # isn't on... it is always the root node
        if node["indent"] == 0:
            total_time += node["duration"]

    return round(total_time, 6)


class IsaacUpdateFrametimeCollector:
    """
    Utility to collect
        app update time (in milliseconds)
        physics update time (in milliseconds)
        gpu frame time (in milliseconds)

    """

    def __init__(self, usd_context_name="", hydra_engine="rtx") -> None:
        try:
            from omni.hydra.engine.stats import HydraEngineStats

            self.hydra_engine_stats = HydraEngineStats(usd_context_name, hydra_engine)
        except:
            self.hydra_engine_stats = None

        try:
            import omni.physx

            self.__physx_benchmarks_iface = omni.physx.get_physx_benchmarks_interface()
        except:
            self.__physx_benchmarks_iface = None
            carb.log_warn("physx interface not loaded, physics frametimes will not be measured")

        self.app_frametimes_ms: List[float] = []
        self.gpu_frametimes_ms: List[float] = []
        self.physics_frametimes_ms: List[float] = []

        self.__last_frametime_timestamp_ns = 0

        self.__subscription: Optional[carb.events.ISubscription] = None
        self.__physx_subscription = None

        self.elapsed_sim_time = 0.0

    def __update_event_callback(self, event: carb.events.IEvent):
        timestamp_ns = time.perf_counter_ns()
        app_update_time_ms = round((timestamp_ns - self.__last_frametime_timestamp_ns) / 1000 / 1000, 6)
        self.__last_frametime_timestamp_ns = timestamp_ns
        gpu_frametime_ms = get_last_gpu_time_ms(self.hydra_engine_stats)
        # print(app_update_time_ms, gpu_frametime_ms)
        self.app_frametimes_ms.append(app_update_time_ms)
        self.gpu_frametimes_ms.append(gpu_frametime_ms)
        self.elapsed_sim_time += event.payload["dt"]

    def __physics_stats_callback(self, profile_stats):
        if len(profile_stats) > 0:
            for stat in profile_stats:
                if stat.zone_name == "PhysX Update":
                    self.physics_frametimes_ms.append(stat.ms)

    def start_collecting(self):
        # reset our tracking variables
        self.app_frametimes_ms: List[float] = []
        self.gpu_frametimes_ms: List[float] = []
        self.physics_frametimes_ms: List[float] = []
        self.__last_frametime_timestamp_ns = time.perf_counter_ns()

        self.__subscription = (
            omni.kit.app.get_app().get_update_event_stream().create_subscription_to_pop(self.__update_event_callback)
        )

        self.__physx_subscription = self.__physx_benchmarks_iface.subscribe_profile_stats_events(
            self.__physics_stats_callback
        )

        self.elapsed_sim_time = 0.0

    def stop_collecting(self) -> Tuple[List[float], List[float], List[float]]:
        self.__subscription = None
        self.__physx_subscription = None

        # drop the first frame since the interval approach doesn't work for
        # the render frame
        if len(self.app_frametimes_ms) > 0:
            self.app_frametimes_ms.pop(0)
        if len(self.gpu_frametimes_ms) > 0:
            self.gpu_frametimes_ms.pop(0)
        if len(self.physics_frametimes_ms) > 0:
            self.physics_frametimes_ms.pop(0)

        # convert s to ms for consistency
        self.elapsed_sim_time *= 1000
        return self.app_frametimes_ms, self.gpu_frametimes_ms, self.physics_frametimes_ms
