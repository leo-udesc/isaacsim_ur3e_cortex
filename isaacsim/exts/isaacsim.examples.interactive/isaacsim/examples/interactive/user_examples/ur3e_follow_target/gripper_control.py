from isaacsim import SimulationApp

simulation_app = SimulationApp({"headless": False})

from omni.isaac.core import World
from omni.isaac.manipulators import SingleManipulator
from omni.isaac.manipulators.grippers import ParallelGripper
from omni.isaac.core.utils.stage import add_reference_to_stage
from omni.isaac.core.utils.types import ArticulationAction
import numpy as np
# sugestão do chat gpt
from omni.isaac.core.utils.prims import get_prim_at_path, get_prim_children


follow_world = World(stage_units_in_meters=1.0)
#TODO: change this to your own path
asset_path = "/home/leo/isaacsim/extension_examples/user_examples/follow_target/ur3e_follow_target.usd"
add_reference_to_stage(usd_path=asset_path, prim_path="/World/ur3e_follow_target")
#define the gripper
# gripper = ParallelGripper(
#    #We chose the following values while inspecting the articulation
#    end_effector_prim_path="/World/ur3e_follow_target/gripper_egh80/gripper_egh80",
#    joint_prim_names=["left_finger_joint", "right_finger_joint"],
#    joint_opened_positions=np.array([0, 0]),
#    joint_closed_positions=np.array([0.04, 0.04]),
#    action_deltas=np.array([0.04, 0.04]),
# )
##define the manipulator
#follow_ur3e = follow_world.scene.add(SingleManipulator(prim_path="/World/ur3e_follow_target", name="ur3e",
#                                                end_effector_prim_name="gripper_egh80/gripper_egh80", gripper=gripper))
##set the default positions of the other gripper joints to be opened so
##that its out of the way of the joints we want to control when gripping an object for instance.
#joints_default_positions = np.zeros(12)
#joints_default_positions[7] = 0.04
#joints_default_positions[8] = 0.04
# follow_ur3e.set_joints_default_state(positions=joints_default_positions)
gripper = ParallelGripper(
    end_effector_prim_path="/World/ur3e_follow_target/ur3e_follow_target/gripper_egh80/gripper_egh80",
    joint_prim_names=["left_finger_joint", "right_finger_joint"],
    joint_opened_positions=np.array([0, 0]),
    joint_closed_positions=np.array([0.04, 0.04]),
    action_deltas=np.array([0.04, 0.04]),
)

follow_ur3e = follow_world.scene.add(
    SingleManipulator(
        prim_path="/World/ur3e_follow_target/ur3e_follow_target",
        name="ur3e",
        end_effector_prim_name="gripper_egh80",  # <-- CORRIGIDO!
        gripper=gripper
    )
)

follow_world.scene.add_default_ground_plane()
follow_world.reset()

import time

# Aguarde alguns frames para garantir que o USD foi carregado
for _ in range(10):
    follow_world.step(render=True)

prim_path = "/World/ur3e_follow_target"
prim = get_prim_at_path(prim_path)
if prim is not None and prim.IsValid():
    print("Prim encontrado:", prim_path)
    print("Filhos:", get_prim_children(prim))  # <-- CORRIGIDO
else:
    print("Prim NÃO encontrado:", prim_path)

prim2_path = "/World/ur3e_follow_target/ur3e_follow_target"
prim2 = get_prim_at_path(prim2_path)
if prim2 is not None and prim2.IsValid():
    print("Filhos de", prim2_path, ":", get_prim_children(prim2))
else:
    print("Prim NÃO encontrado:", prim2_path)

prim3_path = "/World/ur3e_follow_target/ur3e_follow_target/gripper_egh80"
prim3 = get_prim_at_path(prim3_path)
if prim3 is not None and prim3.IsValid():
    print("Filhos de", prim3_path, ":", get_prim_children(prim3))
else:
    print("Prim NÃO encontrado:", prim3_path)
    
prim4_path = "/World/ur3e_follow_target/ur3e_follow_target/gripper_egh80/gripper_egh80"
prim4 = get_prim_at_path(prim4_path)
if prim4 is not None and prim4.IsValid():
    print("Filhos de", prim4_path, ":", get_prim_children(prim4))
else:
    print("Prim NÃO encontrado:", prim4_path)


# chat gpt suggested code

i = 0
while simulation_app.is_running():
    follow_world.step(render=True)
    if follow_world.is_playing():
        if follow_world.current_time_step_index == 0:
            follow_world.reset()
        i += 1
        gripper_positions = follow_ur3e.gripper.get_joint_positions()
        if i < 500:
            #close the gripper slowly
            follow_ur3e.gripper.apply_action(
                ArticulationAction(joint_positions=[gripper_positions[0] + 0.1, gripper_positions[1] - 0.1]))
        if i > 500:
            #open the gripper slowly
            follow_ur3e.gripper.apply_action(
                ArticulationAction(joint_positions=[gripper_positions[0] - 0.1, gripper_positions[1] + 0.1]))
        if i == 1000:
            i = 0

simulation_app.close()