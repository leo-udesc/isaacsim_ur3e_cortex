# Copyright (c) 2022-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
"""Extension to export USD to URDF."""

# Standard Library
import os
import pathlib
from dataclasses import dataclass
from typing import Optional

# Third Party
import numpy as np

# NVIDIA
import omni
import omni.ui as ui
from isaacsim.core.utils.stage import open_stage
from isaacsim.gui.components.element_wrappers import Button, CheckBox, CollapsableFrame, StringField
from isaacsim.gui.components.ui_utils import get_style
from omni.physx import get_physx_property_query_interface
from omni.physx.bindings._physx import PhysxPropertyQueryMode, PhysxPropertyQueryResult
from omni.usd import StageEventType
from pxr import Gf, PhysicsSchemaTools, Sdf, Usd, UsdPhysics, UsdUtils

if os.name == "nt":
    file_dir = pathlib.Path(os.path.dirname(os.path.abspath(__file__)))
    exporter_urdf_dir = file_dir.joinpath(pathlib.Path("../../../../pip_prebundle")).resolve()
    os.add_dll_directory(exporter_urdf_dir.__str__())

import nvidia.srl.tools.logger as logger
import nvidia.srl.usd.prim_helper as prim_helper
from nvidia.srl.from_usd.to_urdf import UsdToUrdf
from nvidia.srl.math.transform import Rotation


class UIBuilder:
    def __init__(self):
        # Frames are sub-windows that can contain multiple UI elements
        self.frames = []
        # UI elements created using a UIElementWrapper instance
        self.wrapped_ui_elements = []

        self.log_level = logger.level_from_name("ERROR")

        self._on_init()

    def _on_init(self):
        self._data_params = dict()
        self._data_params["input_path"] = None
        self._data_params["output_path"] = None
        self._data_params["mesh_dir"] = None
        self._data_params["mesh_path_prefix"] = ""
        self._data_params["use_ros_uri_mesh_path_prefix"] = False
        self._data_params["root"] = None
        self._data_params["visualize_collision_meshes"] = False

    def on_menu_callback(self):
        pass

    def on_stage_event(self, event):
        if event.type == int(StageEventType.OPENED):
            # If the user opens a new stage, the extension should completely reset
            self._reset_extension()

    def cleanup(self):
        for ui_elem in self.wrapped_ui_elements:
            ui_elem.cleanup()

    def build_ui(self):
        def is_usd_path(file_path: str):
            # Filter file paths shown in the file picker to only be USD files
            _, ext = os.path.splitext(file_path.lower())
            return ext == ".usd" or ext == ".usda" or ext == ".usdc"

        def is_urdf_path(file_path: str):
            # Filter file paths shown in the file picker to only be URDF files
            _, ext = os.path.splitext(file_path.lower())
            return ext == ".urdf"

        with ui.VStack(style=get_style(), spacing=5, height=0):
            input_field = StringField(
                "USD Path",
                default_value="",
                tooltip="Path to the USD file to be exported, if empty use current stage",
                read_only=False,
                multiline_okay=False,
                on_value_changed_fn=self._on_input_field_value_changed_fn,
                use_folder_picker=True,
                item_filter_fn=is_usd_path,
                folder_dialog_title="select a USD file",
                folder_button_title="Select File",
            )
            self.wrapped_ui_elements.append(input_field)

            output_field = StringField(
                "Output File/Directory",
                default_value="",
                tooltip="Path to where the URDF file will be created",
                read_only=False,
                multiline_okay=False,
                on_value_changed_fn=self._on_output_field_value_changed_fn,
                use_folder_picker=True,
                item_filter_fn=is_urdf_path,
                folder_dialog_title="Set Output File Or Directory",
                folder_button_title="Select File/Directory",
            )
            self.wrapped_ui_elements.append(output_field)

            button = Button("", "Export", on_click_fn=self._on_export_button_clicked_fn)

            self.wrapped_ui_elements.append(button)

            frame = CollapsableFrame(
                title="Advanced Options",
                collapsed=True,
            )
            self.wrapped_ui_elements.append(frame)
            with frame:
                with ui.VStack(style=get_style(), spacing=5, height=0):
                    mesh_field = StringField(
                        "Mesh Directory Path",
                        default_value="",
                        tooltip="Path to where directory mesh files will be saved. Defaults to 'meshes'.",
                        read_only=False,
                        multiline_okay=False,
                        on_value_changed_fn=self._on_mesh_field_value_changed_fn,
                        use_folder_picker=True,
                        item_filter_fn=is_urdf_path,
                    )
                    self.wrapped_ui_elements.append(mesh_field)

                    self._mesh_path_prefix_field = StringField(
                        "Mesh Path Prefix",
                        default_value="",
                        tooltip="Prefix to add to URDF mesh filename values (e.g. 'file://')",
                        read_only=False,
                        multiline_okay=False,
                        on_value_changed_fn=self._on_mesh_path_prefix_field_value_changed_fn,
                        use_folder_picker=False,
                        item_filter_fn=None,
                    )
                    self.wrapped_ui_elements.append(self._mesh_path_prefix_field)

                    use_ros_uri_mesh_path_prefix_check_box = CheckBox(
                        "Use ROS Mesh Path Prefix",
                        default_value=False,
                        tooltip="Set the mesh path prefix to file://<path to mesh directory path>.",
                        on_click_fn=self._on_use_ros_uri_mesh_path_prefix_check_box_click_fn,
                    )
                    self.wrapped_ui_elements.append(use_ros_uri_mesh_path_prefix_check_box)

                    root_path_field = StringField(
                        "Root Prim Path",
                        default_value="",
                        tooltip="Root prim path of the robot to be exported. Defaults to the default prim.",
                        read_only=False,
                        multiline_okay=False,
                        on_value_changed_fn=self._on_root_field_value_changed_fn,
                        use_folder_picker=False,
                        item_filter_fn=None,
                    )
                    self.wrapped_ui_elements.append(root_path_field)

                    stage_visualize_collisions_check_box = CheckBox(
                        "Visualize Collisions",
                        default_value=False,
                        tooltip="Visualization collider meshes even if their visibility is disabled.",
                        on_click_fn=self._on_visualize_collisions_check_box_click_fn,
                    )
                    self.wrapped_ui_elements.append(stage_visualize_collisions_check_box)

    def _on_input_field_value_changed_fn(self, new_value: str):
        self._data_params["input_path"] = new_value

    def _on_output_field_value_changed_fn(self, new_value: str):
        self._data_params["output_path"] = new_value

    def _on_mesh_path_prefix_field_value_changed_fn(self, new_value: str):
        self._data_params["mesh_path_prefix"] = new_value

    def _on_use_ros_uri_mesh_path_prefix_check_box_click_fn(self, value: bool):
        self._data_params["use_ros_uri_mesh_path_prefix"] = value

        if value:
            self._mesh_path_prefix_field_prev_val = self._mesh_path_prefix_field.get_value()
            self._mesh_path_prefix_field.set_value("file://<path to output directory>")
        else:
            self._mesh_path_prefix_field.set_value(self._mesh_path_prefix_field_prev_val)
        self._mesh_path_prefix_field.enabled = not value

    def _on_root_field_value_changed_fn(self, new_value: str):
        self._data_params["root"] = new_value

    def _on_mesh_field_value_changed_fn(self, new_value: str):
        self._data_params["mesh_dir"] = new_value

    def _on_visualize_collisions_check_box_click_fn(self, value: bool):
        self._data_params["visualize_collision_meshes"] = value

    def _on_export_button_clicked_fn(self):
        root = self._data_params["root"]
        if root == "":
            root = None

        usd_to_urdf_kwargs = {
            "node_names_to_remove": None,
            "edge_names_to_remove": None,
            "root": root,
            "parent_link_is_body_1": None,
            "log_level": self.log_level,
        }

        usd_path = self._data_params["input_path"]
        if usd_path == "":
            usd_path = None

        if usd_path is None:
            stage = omni.usd.get_context().get_stage()

            # Get stage path
            input_path = stage.GetRootLayer().realPath

            # Create a new USD layer to store inertia data
            inertia_temp_layer = Sdf.Layer.CreateAnonymous("inertia_temp.usda")

            # Set the new layer as the edit target
            root_layer = stage.GetRootLayer()
            root_layer.subLayerPaths.append(inertia_temp_layer.identifier)
            stage.SetEditTarget(Usd.EditTarget(inertia_temp_layer))

            # Set the inertia values for the prims in the new layer
            inertia_prims = prim_helper.get_prims(stage, has_apis=[UsdPhysics.MassAPI, UsdPhysics.RigidBodyAPI])

            for prim in inertia_prims:
                inertia_data = InertiaData.init_from_prim(prim)
                mass_api = UsdPhysics.MassAPI(prim)

                # Set the mass
                mass_api.GetMassAttr().Set(inertia_data.mass)

                # Set the center of mass
                x = float(inertia_data.ref_point[0])
                y = float(inertia_data.ref_point[1])
                z = float(inertia_data.ref_point[2])
                mass_api.GetCenterOfMassAttr().Set(Gf.Vec3f(x, y, z))

                # Set the inertia diagonal
                x = float(inertia_data.inertia_diag[0])
                y = float(inertia_data.inertia_diag[1])
                z = float(inertia_data.inertia_diag[2])
                mass_api.GetDiagonalInertiaAttr().Set(Gf.Vec3f(x, y, z))

                # Set the principal axes
                quat = inertia_data.prin_axes.as_quat()
                w = float(quat[3])
                x = float(quat[0])
                y = float(quat[1])
                z = float(quat[2])
                mass_api.GetPrincipalAxesAttr().Set(Gf.Quatf(w, (x, y, z)))

            # Create the UsdToUrdf object with the inertia data in the stage
            usd_to_urdf = UsdToUrdf(stage, **usd_to_urdf_kwargs)
        else:
            input_path = usd_path
            usd_to_urdf = UsdToUrdf.init_from_file(usd_path, **usd_to_urdf_kwargs)

        urdf_output_path = self._data_params["output_path"]
        if urdf_output_path == "" or urdf_output_path is None:
            if input_path is None:
                raise ValueError("Must specify an URDF output path.")
            urdf_output_path = pathlib.Path(input_path).parent

        mesh_dir = self._data_params["mesh_dir"]
        if mesh_dir == "":
            mesh_dir = None

        output_path = usd_to_urdf.save_to_file(
            urdf_output_path=urdf_output_path,
            visualize_collision_meshes=self._data_params["visualize_collision_meshes"],
            mesh_dir=mesh_dir,
            mesh_path_prefix=self._data_params["mesh_path_prefix"],
            use_uri_file_prefix=self._data_params["use_ros_uri_mesh_path_prefix"],
        )

        if usd_path is None:
            # Revert the stage back to its original state by removing the new layer if it was added
            root_layer.subLayerPaths.remove(inertia_temp_layer.identifier)
            stage.SetEditTarget(stage.GetRootLayer())

        print("Converted USD to URDF.")
        print(f"    Input: {input_path}")
        print(f"    Output: {output_path}")

    def _reset_extension(self):
        pass


@dataclass
class InertiaData:
    """Helper class to store inertia data."""

    mass: Optional[float] = None
    ref_point: Optional[np.ndarray] = None
    inertia_diag: Optional[np.ndarray] = None
    prin_axes: Optional[Rotation] = None

    @classmethod
    def get_physx_queried_inertia_data(cls, prim) -> "InertiaData":
        inertia_data = cls()

        def rigid_body_fn(rigid_info, prim_path: str):
            nonlocal inertia_data

            if rigid_info.result == PhysxPropertyQueryResult.VALID:
                inertia_data.mass = rigid_info.mass
                inertia_data.ref_point = np.array(rigid_info.center_of_mass)
                inertia_data.inertia_diag = np.array(rigid_info.inertia)

                prin_axes_quat = np.array(
                    [
                        rigid_info.principal_axes[3],
                        rigid_info.principal_axes[0],
                        rigid_info.principal_axes[1],
                        rigid_info.principal_axes[2],
                    ]
                )
                try:
                    inertia_data.prin_axes = Rotation.from_quat(prin_axes_quat)
                except ValueError:
                    inertia_data.prin_axes = None
            else:
                raise RuntimeError(f"PhysX query rigid info is not valid for the given prim: '{prim_path}'")

        stage = prim.GetStage()
        stage_cache = UsdUtils.StageCache().Get()
        stage_id = stage_cache.GetId(stage).ToLongInt()
        prim_path = str(prim.GetPath())
        prim_id = PhysicsSchemaTools.sdfPathToInt(prim_path)

        get_physx_property_query_interface().query_prim(
            stage_id=stage_id,
            prim_id=prim_id,
            query_mode=PhysxPropertyQueryMode.QUERY_RIGID_BODY_WITH_COLLIDERS,
            rigid_body_fn=lambda rigid_info: rigid_body_fn(rigid_info, prim_path=prim_path),
        )

        return inertia_data

    @classmethod
    def init_from_prim(cls, prim):
        inertia_data = cls.get_physx_queried_inertia_data(prim)

        mass_api = UsdPhysics.MassAPI(prim)

        mass_attr = mass_api.GetMassAttr()
        if mass_attr.IsValid() and mass_attr.HasValue() and mass_attr.HasAuthoredValue():
            inertia_data.mass = mass_attr.Get()

        ref_point_attr = mass_api.GetCenterOfMassAttr()
        if ref_point_attr.IsValid() and ref_point_attr.HasValue() and ref_point_attr.HasAuthoredValue():
            inertia_data.ref_point = np.array(ref_point_attr.Get())

        inertia_diag_attr = mass_api.GetDiagonalInertiaAttr()
        if inertia_diag_attr.IsValid() and inertia_diag_attr.HasValue() and inertia_diag_attr.HasAuthoredValue():
            inertia_data.inertia_diag = np.array(inertia_diag_attr.Get())

        prin_axes_attr = mass_api.GetPrincipalAxesAttr()
        if prin_axes_attr.IsValid() and prin_axes_attr.HasValue() and prin_axes_attr.HasAuthoredValue():
            prin_axes_gf_quat = mass_api.GetPrincipalAxesAttr().Get()
            prin_axes_quat = np.array(list(prin_axes_gf_quat.GetImaginary()) + [prin_axes_gf_quat.GetReal()])
            try:
                inertia_data.prin_axes = Rotation.from_quat(prin_axes_quat)
            except ValueError:
                pass

        return inertia_data


def create_new_stage_with_inertia_data(stage):
    link_prims = prim_helper.get_prims(stage, has_apis=[UsdPhysics.MassAPI, UsdPhysics.RigidBodyAPI])

    for prim in link_prims:
        inertia_data = InertiaData.init_from_prim(prim)
        mass_api = UsdPhysics.MassAPI(prim)

        # Set the mass
        mass_api.GetMassAttr().Set(inertia_data.mass)

        # Set the center of mass
        x = float(inertia_data.ref_point[0])
        y = float(inertia_data.ref_point[1])
        z = float(inertia_data.ref_point[2])
        mass_api.GetCenterOfMassAttr().Set(Gf.Vec3f(x, y, z))

        # Set the inertia diagonal
        x = float(inertia_data.inertia_diag[0])
        y = float(inertia_data.inertia_diag[1])
        z = float(inertia_data.inertia_diag[2])
        mass_api.GetDiagonalInertiaAttr().Set(Gf.Vec3f(x, y, z))

        # Set the principal axes
        quat = inertia_data.prin_axes.as_quat()
        w = float(quat[3])
        x = float(quat[0])
        y = float(quat[1])
        z = float(quat[2])
        mass_api.GetPrincipalAxesAttr().Set(Gf.Quatf(w, (x, y, z)))

    return stage
