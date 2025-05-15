# UR3e CUBE BOXING EXAMPLE
# 1. Inicalizar a aplicação do Isaac Sim
# 2. Criar o mundo (CortexWorld)
# 3. Adicionar o robô UR3e ao mundo
# 4. Adicionar os cubos ao mundo
# 5. Adicionar o plano de solo ao mundo
# 6. Adicionar as caixas ao mundo
# 7. Carregar o comportamento do robô
# 8. Adicionar a rede de decisão (associada ao comportamento) ao mundo
# 9. Executar a simulação

import argparse

from isaacsim import SimulationApp

parser = argparse.ArgumentParser("ur3e_examples")
parser.add_argument(
    "--behavior",
    type=str,
    default="block_allocation_behavior",
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
from cube_manager import CubeManager





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

    # Create cube manager and initialize
    cube_manager = CubeManager(world, robot)
    cube_manager.create_cycle_cubes()
    
    world.scene.add_default_ground_plane()

    # Create boxes
    box_configs = [
        {
            "name": "bluebox",
            "usd_path": "/home/leo/isaacsim/extension_examples/user_examples/onshape_usd_imported/objects/box/bluebox.usd",
            "angle": 0  # First position
        },
        {
            "name": "redbox",
            "usd_path": "/home/leo/isaacsim/extension_examples/user_examples/onshape_usd_imported/objects/box/redbox.usd",
            "angle": 30  # Second position
        },
        {
            "name": "yellowbox",
            "usd_path": "/home/leo/isaacsim/extension_examples/user_examples/onshape_usd_imported/objects/box/yellowbox.usd",
            "angle": 60  # Third position
        },
        {
            "name": "greenbox",
            "usd_path": "/home/leo/isaacsim/extension_examples/user_examples/onshape_usd_imported/objects/box/greenbox.usd",
            "angle": 90  # Fourth position
        }
    ]

    radius = 0.4  # 400mm in meters
    boxes = {}
    
    for box_config in box_configs:
        # Convert angle to radians and calculate position
        angle_rad = np.radians(box_config["angle"])
        
        # Calculate positions using standard trigonometry
        x = radius * np.sin(angle_rad)  # x = r * sin(θ)
        y = radius * np.cos(angle_rad)  # y = r * cos(θ)
        
        # Add box to scene
        box = world.scene.add(
            VisualCuboid(
                prim_path=f"/World/Boxes/{box_config['name']}",
                name=box_config['name'],
                position=np.array([x, y, 0.0]),
                orientation=np.array([0.0, 0.0, angle_rad]),  # Orient box to face center
                usd_path=box_config['usd_path']
            )
        )
        boxes[box_config['name']] = box

    
    print()
    print("loading behavior: {}".format(args.behavior))
    print()
    if args.behavior in behaviors:
        decider_network = behaviors[args.behavior].make_decider_network(robot)
    else:
        decider_network = load_behavior_module(args.behavior).make_decider_network(robot)
    decider_network.context.add_monitor(context_monitor.monitor)
    world.add_decider_network(decider_network)

    world.run(simulation_app)
    while not cube_manager.is_complete():
        cube_manager.check_and_replace_cubes()
    simulation_app.close()


if __name__ == "__main__":
    main()
