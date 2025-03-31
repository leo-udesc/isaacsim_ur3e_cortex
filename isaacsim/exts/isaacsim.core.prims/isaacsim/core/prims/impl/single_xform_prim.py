# Copyright (c) 2021-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from typing import Optional, Sequence

import carb
from isaacsim.core.utils.prims import define_prim, get_prim_at_path, is_prim_path_valid

from ._impl.single_prim_wrapper import _SinglePrimWrapper
from .xform_prim import XFormPrim


class SingleXFormPrim(_SinglePrimWrapper):
    """Provides high level functions to deal with an Xform prim (only one Xform prim) and its attributes/properties

    If there is an Xform prim present at the path, it will use it. Otherwise, a new XForm prim at
    the specified prim path will be created

    .. note::

        The prim will have ``xformOp:orient``, ``xformOp:translate`` and ``xformOp:scale`` only post-init,
        unless it is a non-root articulation link.

    Args:
        prim_path (str): prim path of the Prim to encapsulate or create.
        name (str, optional): shortname to be used as a key by Scene class.
                                Note: needs to be unique if the object is added to the Scene.
                                Defaults to "xform_prim".
        position (Optional[Sequence[float]], optional): position in the world frame of the prim. shape is (3, ).
                                                    Defaults to None, which means left unchanged.
        translation (Optional[Sequence[float]], optional): translation in the local frame of the prim
                                                        (with respect to its parent prim). shape is (3, ).
                                                        Defaults to None, which means left unchanged.
        orientation (Optional[Sequence[float]], optional): quaternion orientation in the world/ local frame of the prim
                                                        (depends if translation or position is specified).
                                                        quaternion is scalar-first (w, x, y, z). shape is (4, ).
                                                        Defaults to None, which means left unchanged.
        scale (Optional[Sequence[float]], optional): local scale to be applied to the prim's dimensions. shape is (3, ).
                                                Defaults to None, which means left unchanged.
        visible (bool, optional): set to false for an invisible prim in the stage while rendering. Defaults to True.

    Raises:
        Exception: if translation and position defined at the same time

    Example:

    .. code-block:: python

        >>> from isaacsim.core.prims import SingleXFormPrim
        >>>
        >>> # given the stage: /World. Get the Xform prim at /World
        >>> prim = SingleXFormPrim("/World")
        >>> prim
        <isaacsim.core.prims.single_xform_prim.SingleXFormPrim object at 0x7f52381547c0>
        >>>
        >>> # create a new Xform prim at path: /World/Objects
        >>> prim = SingleXFormPrim("/World/Objects", name="objects")
        >>> prim
        <isaacsim.core.prims.single_xform_prim.SingleXFormPrim object at 0x7f525c11d420>
    """

    def __init__(
        self,
        prim_path: str,
        name: str = "xform_prim",
        position: Optional[Sequence[float]] = None,
        translation: Optional[Sequence[float]] = None,
        orientation: Optional[Sequence[float]] = None,
        scale: Optional[Sequence[float]] = None,
        visible: Optional[bool] = None,
    ) -> None:

        if is_prim_path_valid(prim_path):
            self._prim = get_prim_at_path(prim_path)
        else:
            carb.log_info("Creating a new XForm prim at path {}".format(prim_path))
            self._prim = define_prim(prim_path=prim_path, prim_type="Xform")

        from isaacsim.core.simulation_manager import SimulationManager

        self._backend = SimulationManager.get_backend()
        self._device = SimulationManager.get_physics_sim_device()
        self._backend_utils = SimulationManager._get_backend_utils()
        if position is not None:
            position = self._backend_utils.convert(position, self._device)
            position = self._backend_utils.expand_dims(position, 0)
        if translation is not None:
            translation = self._backend_utils.convert(translation, self._device)
            translation = self._backend_utils.expand_dims(translation, 0)
        if orientation is not None:
            orientation = self._backend_utils.convert(orientation, self._device)
            orientation = self._backend_utils.expand_dims(orientation, 0)
        if scale is not None:
            scale = self._backend_utils.convert(scale, self._device)
            scale = self._backend_utils.expand_dims(scale, 0)
        if visible is not None:
            visible = self._backend_utils.create_tensor_from_list([visible], dtype="bool", device=self._device)
        self._xform_prim_view = XFormPrim(
            prim_paths_expr=prim_path,
            name=name,
            positions=position,
            translations=translation,
            orientations=orientation,
            scales=scale,
            visibilities=visible,
        )
        self._binding_api = None
        _SinglePrimWrapper.__init__(self, view=self._xform_prim_view)
        return
