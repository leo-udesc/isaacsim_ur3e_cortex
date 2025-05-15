import numpy as np
from isaacsim.core.api.objects import DynamicCuboid
import itertools

class CubeManager:
    def __init__(self, world, robot):
        self.world = world
        self.robot = robot
        self.width = 0.04
        self.y_pos = -0.3
        
        # Define cube specifications
        self.cube_specs = {
            "RedCube": [0.7, 0.0, 0.0],
            "BlueCube": [0.0, 0.0, 0.7],
            "YellowCube": [0.7, 0.7, 0.0],
            "GreenCube": [0.0, 0.7, 0.0]
        }
        
        # Track current cycle and cubes
        self.cycle_count = 0
        self.active_cubes = {}
        
        # Generate all possible color permutations
        self.names = list(self.cube_specs.keys())
        self.colors = list(self.cube_specs.values())
        self.color_permutations = list(itertools.permutations(self.colors))
        self.current_permutation = 0
        
        # Fixed positions from ur3e_examples_main.py
        self.x_positions = np.linspace(0.1, 0.4, len(self.cube_specs))

    def create_cycle_cubes(self):
        """Create new set of cubes with permuted colors"""
        # Clear any existing cubes
        self.active_cubes.clear()
        
        # Get next color permutation
        colors = self.color_permutations[self.current_permutation]
        self.current_permutation = (self.current_permutation + 1) % len(self.color_permutations)
        
        # Create cubes with permuted colors at fixed positions
        for name, x, color in zip(self.names, self.x_positions, colors):
            position = np.array([x, self.y_pos, self.width / 2.0])
            
            # Create cube with cycle count in name for uniqueness
            cube_name = f"{name}_{self.cycle_count}"
            obj = self.world.scene.add(
                DynamicCuboid(
                    prim_path=f"/World/Obs/{cube_name}",
                    name=cube_name,
                    size=self.width,
                    color=np.array(color),
                    position=position
                )
            )
            self.robot.register_obstacle(obj)
            self.active_cubes[cube_name] = obj
            
        self.cycle_count += 1
        print(f"Created cubes for cycle {self.cycle_count}")

    def check_cubes_allocated(self):
        """Check if all current cubes have been allocated to boxes"""
        for cube in self.active_cubes.values():
            if cube.get_world_pose()[0][2] < 0.1:  # Check if cube is still at original height
                return False
        return True

    def cleanup_cycle(self):
        """Clean up after cycle completion"""
        self.active_cubes.clear()