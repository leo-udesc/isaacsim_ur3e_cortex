import argparse
import time
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

time.sleep(0.01)

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

def create_cubes(world, robot, cycle_count):
    """Create new set of cubes with base names"""
    width = 0.04
    obs_specs = [
        CubeSpec("RedCube", [0.7, 0.0, 0.0]),    # 
        CubeSpec("BlueCube", [0.0, 0.0, 0.7]),   # 
        CubeSpec("YellowCube", [0.7, 0.7, 0.0]), # 
        CubeSpec("GreenCube", [0.0, 0.7, 0.0]),  #
    ]
    
    print("loading blocks")
    for i, (x, spec) in enumerate(zip(np.linspace(0.1, 0.4, len(obs_specs)), obs_specs)):
        obj = world.scene.add(
            DynamicCuboid(
                prim_path=f"/World/Obs/{spec.name}_{cycle_count}", 
                name=spec.name,  
                size=width,
                color=spec.color,
                position=np.array([x, -0.3, width / 2.0]),
            )
        )
        print(f"{i}) {spec.name}")
        robot.register_obstacle(obj)
    print("====================================\n")


def main():
    world = CortexWorld()
    context_monitor = ContextStateMonitor(print_dt=0.25)
    
    # Add robot
    robot = world.add_robot(add_ur3e_to_stage(
        name="ur3e",
        prim_path="/World/ur3e",
        usd_path="/home/leo/ws_isaacsim/ur3e/usd/ur3e.usd"
    ))

    # Tower positions
    tower_positions = [
        np.array([0.0, 0.3, 0.0]),
        np.array([0.1, 0.3, 0.0]),
        np.array([0.2, 0.3, 0.0]),
        np.array([0.3, 0.3, 0.0])
    ]
    current_tower = 0
    cycle_count = 0

    # Create initial cubes
    create_cubes(world, robot, cycle_count)
    
    world.scene.add_default_ground_plane()
    
    print("loading behavior: {}".format(args.behavior))
    
    # Create initial decider network with first tower position
    if args.behavior in behaviors:
        decider_network = behaviors[args.behavior].make_decider_network(robot, tower_positions[current_tower])
    else:
        decider_network = load_behavior_module(args.behavior).make_decider_network(robot, tower_positions[current_tower])
    
    decider_network.context.add_monitor(context_monitor.monitor)
    world.add_decider_network(decider_network)

    rate = SteadyRate(60)  # 60Hz update rate
    
    # Run simulation with tower updates
    while simulation_app.is_running():
        try:
            # Step the world
            world.step(render=True)
            
            # Check tower completion
            if decider_network.context.block_tower.is_complete:
                print(f"Tower {current_tower + 1} completed")
                current_tower += 1
                
                if current_tower >= len(tower_positions):
                    print("All towers completed!")
                    break
                    
                print(f"Starting tower {current_tower + 1}")
                cycle_count += 1
                
                # Remove old cubes before creating new ones
                world.scene.clear_obstacles()
                create_cubes(world, robot, cycle_count)
                
                # Create new decider network with next tower position
                if args.behavior in behaviors:
                    decider_network = behaviors[args.behavior].make_decider_network(
                        robot, tower_positions[current_tower]
                    )
                else:
                    decider_network = load_behavior_module(args.behavior).make_decider_network(
                        robot, tower_positions[current_tower]
                    )
                
                decider_network.context.add_monitor(context_monitor.monitor)
                world.add_decider_network(decider_network)
            
            rate.sleep()
            
        except Exception as e:
            print(f"Error in simulation loop: {e}")
            raise  # Re-raise exception for better debugging
            
    simulation_app.close()


if __name__ == "__main__":
    main()