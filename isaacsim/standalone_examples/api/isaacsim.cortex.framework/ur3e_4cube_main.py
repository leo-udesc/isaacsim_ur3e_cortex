# Copyright (c) 2022-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import argparse

from isaacsim import SimulationApp

parser = argparse.ArgumentParser("ur3e_examples")
parser.add_argument(
    "--behavior",
    type=str,
    default="block_stacking_behavior",
    help="Which behavior to run. See behavior/ur3e for available behavior files.",
)
args, _ = parser.parse_known_args()

simulation_app = SimulationApp({"headless": False})

import numpy as np
from behaviors.ur3e.ur3e_behaviors import ContextStateMonitor, behaviors
from isaacsim.core.api.objects import DynamicCuboid, VisualCuboid
from isaacsim.cortex.framework.cortex_utils import load_behavior_module
from isaacsim.cortex.framework.cortex_world import Behavior, CortexWorld, LogicalStateMonitor
from isaacsim.cortex.framework.robot import add_ur3e_to_stage
from isaacsim.cortex.framework.tools import SteadyRate


class CubeSpec:
    def __init__(self, name, color):
        self.name = name
        self.color = np.array(color)



def main():
    world = CortexWorld()
    context_monitor = ContextStateMonitor(print_dt=0.25)
    # Load the UR3e robot
    # Adiciona o robô UR3e ao mundo 
    robot = world.add_robot(add_ur3e_to_stage(
        name="ur3e",
        prim_path="/World/ur3e",
        usd_path="/home/leo/ws_isaacsim/ur3e/usd/ur3e.usd"

    ))

    # Adiciona os cubos
    obs_specs = [
        CubeSpec("RedCube", [0.7, 0.0, 0.0]),
        CubeSpec("BlueCube", [0.0, 0.0, 0.7]),
        CubeSpec("YellowCube", [0.7, 0.7, 0.0]),
        CubeSpec("GreenCube", [0.0, 0.7, 0.0]),
    ]
    width = 0.04

    # # # Cria 4 pilhas de cubos da mesma cor
    for stack_idx, x in enumerate(np.linspace(0.15, 0.3, 4)):
        # Usa a mesma especificação (cor) para todos os cubos da pilha
        spec = obs_specs[stack_idx]
        print(f"\nCriando pilha {stack_idx + 1} na posição x={x:.2f} com cor {spec.name}")
        
        for cube_idx in range(4):
            # Nome único para cada cubo
            cube_name = f"{spec.name}_{stack_idx}_{cube_idx}"
            
            obj = world.scene.add(
                DynamicCuboid(
                    prim_path=f"/World/Obs/{spec.name}_{stack_idx}_{cube_idx}",
                    name=cube_name,  # Nome único para cada cubo
                    size=width,
                    color=spec.color,
                    position=np.array([x, -0.3, width/2.0 + (cube_idx * width)]),
                )
            )
            print(f"  {cube_idx}) {cube_name}")
            robot.register_obstacle(obj)

    #====================================================================
    #Original com 4 cubos em linha  (rodando até o fim)
    # for i, (x, spec) in enumerate(zip(np.linspace(0.1, 0.4, len(obs_specs)), obs_specs)):
    #     obj = world.scene.add(
    #         DynamicCuboid(
    #             prim_path="/World/Obs/{}".format(spec.name),
    #             name=spec.name,
    #             size=width,
    #             color=spec.color,
    #             position=np.array([x, -0.3, width / 2.0]),
    #         )
    #     )
    #     robot.register_obstacle(obj)
   

    world.scene.add_default_ground_plane()

    print()
    print("loading behavior: {}".format(args.behavior))
    print()
    tower_position = np.array([0.1, 0.3, 0.0])
    if args.behavior in behaviors:
        decider_network = behaviors[args.behavior].make_decider_network(robot,tower_position)
    else:
        decider_network = load_behavior_module(args.behavior).make_decider_network(robot,tower_position)
    decider_network.context.add_monitor(context_monitor.monitor)
    world.add_decider_network(decider_network)

    world.run(simulation_app)
    simulation_app.close()


if __name__ == "__main__":
    main()
