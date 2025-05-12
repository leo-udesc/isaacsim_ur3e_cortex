#1. Identificar os blocos no ambiente (world.scene)
#2. Decidir qual bloco pegar, priorizando a ordem de chegada no ambiente
#3. Calcular a melhor posição "pose" para pegar o bloco (grasp) escolhido
#4. Mover gripper e robô para a posição do bloco (pose(grasp))
#5. Pegar o bloco (grasp)
#6. Decidir onde colocar o bloco:
#          bloco azul --> caixa azul
#          bloco vermelho --> caixa vermelha
#          bloco amarelo --> caixa amarela
#          bloco verde --> caixa verde 
# 7. Mover gripper, robô e bloco para a posição da caixa (pose(box)) 
#8. a) Soltar no centro da caixa
#   b) construir torre de blocos e registrar a proxima posição livre
#9. Repetir o processo até que em todas as caixas tenham 18 cubos alocados
#10. Se não houver mais blocos, parar o robô

import argparse
import copy
import math
import random
import sys
import time
from collections import OrderedDict

import isaacsim.cortex.framework.math_util as math_util
import numpy as np
from isaacsim.cortex.framework.cortex_object import CortexObject
from isaacsim.cortex.framework.df import *
from isaacsim.cortex.framework.dfb import (
    DfApproachGrasp,
    DfCloseGripper,
    DfOpenGripper,
    DfRobotApiContext,
    make_go_home,
)
from isaacsim.cortex.framework.motion_commander import MotionCommand, PosePq


class Block:
    def __init__(self, obj):
        self.obj = obj
        self.name = obj.name
        self.arrival_time = time.time()
        self.chosen_grasp = None
        self.color = obj.get_color()

    @property
    def has_chosen_grasp(self):
        return self.chosen_grasp is not None

    def get_best_grasp(self, eff_T, other_obj_Ts):
        obj_T = self.obj.get_transform()
        return get_best_obj_grasp(obj_T, make_block_grasp_Ts(0.02), eff_T, other_obj_Ts)

class ColorBox:
    def __init__(self, obj, color):
        """
        Initialize ColorBox with existing box object
        Args:
            obj: Box object from scene
            color: RGB color array for matching blocks
        """
        self.box_obj = obj
        self.color = np.array(color)
        self.blocks = []
        self.current_layer = 0
        self.layer_size = 9  # 3x3 grid per layer
        self.max_layers = 2  # 2 layers of 9 blocks each
        self.block_width = 0.04
        self.base_position = obj.get_world_pose()[0]  # Get box position from scene

    def get_next_position(self):
        """Calculate next available position in box grid"""
        if self.is_full:
            return None
            
        num_blocks = len(self.blocks)
        layer = num_blocks // self.layer_size
        pos_in_layer = num_blocks % self.layer_size
        
        # Calculate grid position
        row = pos_in_layer // 3
        col = pos_in_layer % 3
        
        # Calculate offset from box center
        box_dims = self.box_obj.get_shape_params()["size"]
        offset = np.array([
            (col - 1) * (self.block_width + 0.01),  # X with spacing
            (row - 1) * (self.block_width + 0.01),  # Y with spacing
            box_dims[2] + (layer * self.block_width)  # Z from box bottom
        ])
        
        return self.base_position + offset

    def add_block(self, block):
        """Add block and return target position"""
        if self.is_full:
            return None
            
        self.blocks.append(block)
        return self.get_next_position()

    @property
    def is_full(self):
        """Check if box has reached 18 block capacity"""
        return len(self.blocks) >= (self.layer_size * self.max_layers)
        
    def get_color_match_score(self, block_color):
        """Calculate how well a block color matches this box"""
        return -np.linalg.norm(self.color - block_color)

class AllocationContext(DfRobotApiContext):
    def __init__(self, robot):
        super().__init__(robot)
        self.blocks = {}
        self.active_block = None
        self.in_gripper = None
        self.boxes = self._initialize_boxes()

    def _initialize_boxes(self):
        """Find and initialize storage boxes from scene"""
        boxes = {}
        scene_boxes = self.world.scene.get_objects_by_type("StaticCuboid")  # or appropriate type
        
        # Color mapping for boxes
        box_colors = {
            "blue_box": [0.0, 0.0, 0.7],
            "red_box": [0.7, 0.0, 0.0],
            "yellow_box": [0.7, 0.7, 0.0],
            "green_box": [0.0, 0.7, 0.0]
        }
        
        for box_obj in scene_boxes:
            for name, color in box_colors.items():
                if name in box_obj.name.lower():
                    boxes[name] = ColorBox(box_obj, color)
                    break
                    
        return boxes

class BlockAllocationDispatch(DfDecider):
    def __init__(self):
        super().__init__()
        self.add_child("pick", make_pick_rlds())
        self.add_child("place", make_place_rlds())
        self.add_child("go_home", make_go_home())

    def decide(self):
        ct = self.context
        ct.scan_environment()

        if ct.in_gripper:
            ct.target_box = ct.find_target_box(ct.in_gripper)
            return DfDecision("place")
        elif len(ct.blocks) > 0:
            return DfDecision("pick")
        else:
            return DfDecision("go_home")

def make_pick_rlds():
    """Create pick behavior sequence"""
    rlds = DfRldsDecider()
    rlds.add_child("open_gripper", DfOpenGripper())
    rlds.add_child("approach_grasp", DfApproachGrasp())
    rlds.add_child("close_gripper", DfCloseGripper())
    return rlds

def make_place_rlds():
    """Create place behavior sequence"""
    rlds = DfRldsDecider()
    rlds.add_child("move_to_box", DfApproachGrasp())
    rlds.add_child("open_gripper", DfOpenGripper())
    rlds.add_child("retract", make_go_home())
    return rlds

def make_decider_network(robot):
    """Create the complete allocation network"""
    context = AllocationContext(robot)
    dispatch = BlockAllocationDispatch()
    return DfNetwork(dispatch, context=context)
