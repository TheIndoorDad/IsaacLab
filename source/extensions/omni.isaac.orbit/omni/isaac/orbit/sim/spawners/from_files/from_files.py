# Copyright (c) 2022, NVIDIA CORPORATION & AFFILIATES, ETH Zurich, and University of Toronto
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from typing import TYPE_CHECKING

import carb
import omni.isaac.core.utils.prims as prim_utils
import omni.kit.commands
from pxr import Gf, Sdf, Usd

from omni.isaac.orbit.sim import loaders, schemas
from omni.isaac.orbit.sim.utils import bind_physics_material, clone

if TYPE_CHECKING:
    from . import from_files_cfg


@clone
def spawn_from_usd(
    prim_path: str,
    cfg: from_files_cfg.UsdFileCfg,
    translation: tuple[float, float, float] | None = None,
    orientation: tuple[float, float, float, float] | None = None,
    scale: tuple[float, float, float] | None = None,
) -> Usd.Prim:
    """Spawn an asset from a USD file and override the settings with the given config.

    In the case of a USD file, the asset is spawned at the default prim specified in the USD file.
    If a default prim is not specified, then the asset is spawned at the root prim.

    In case a prim already exists at the given prim path, then the function does not create a new prim
    or throw an error that the prim already exists. Instead, it just takes the existing prim and overrides
    the settings with the given config.

    .. note::
        This function is decorated with :func:`clone` that resolves prim path into list of paths
        if the input prim path is a regex pattern. This is done to support spawning multiple assets
        from a single and cloning the USD prim at the given path expression.

    Args:
        prim_path: The prim path or pattern to spawn the asset at. If the prim path is a regex pattern,
            then the asset is spawned at all the matching prim paths.
        cfg: The configuration instance.
        translation: The translation to apply to the prim
            w.r.t. its parent prim. Defaults to None.
        orientation: The orientation in (w, x, y, z) to apply to
            the prim w.r.t. its parent prim. Defaults to None.
        scale: The scale of the imported prim. Defaults to None.

    Returns:
        The prim of the spawned asset.
    """
    # -- spawn asset if it doesn't exist.
    if not prim_utils.is_prim_path_valid(prim_path):
        # add prim as reference to stage
        prim_utils.create_prim(
            prim_path,
            usd_path=cfg.usd_path,
            translation=translation,
            orientation=orientation,
            scale=scale,
        )
    else:
        carb.log_warn(f"A prim already exists at prim path: '{prim_path}'.")

    # modify rigid body properties
    if cfg.rigid_props is not None:
        schemas.modify_rigid_body_properties(prim_path, cfg.rigid_props)
    # modify collision properties
    if cfg.collision_props is not None:
        schemas.modify_collision_properties(prim_path, cfg.collision_props)
    # modify articulation root properties
    if cfg.articulation_props is not None:
        schemas.modify_articulation_root_properties(prim_path, cfg.articulation_props)
    # return the prim
    return prim_utils.get_prim_at_path(prim_path)


@clone
def spawn_from_urdf(
    prim_path: str,
    cfg: from_files_cfg.UrdfFileCfg,
    translation: tuple[float, float, float] | None = None,
    orientation: tuple[float, float, float, float] | None = None,
    scale: tuple[float, float, float] | None = None,
) -> Usd.Prim:
    """Spawn an asset from a URDF file and override the settings with the given config.

    It uses the :class:`UrdfLoader` class to create a USD file from URDF. This file is then imported
    at the specified prim path.

    In case a prim already exists at the given prim path, then the function does not create a new prim
    or throw an error that the prim already exists. Instead, it just takes the existing prim and overrides
    the settings with the given config.

    .. note::
        This function is decorated with :func:`clone` that resolves prim path into list of paths
        if the input prim path is a regex pattern. This is done to support spawning multiple assets
        from a single and cloning the USD prim at the given path expression.

    Args:
        prim_path: The prim path or pattern to spawn the asset at. If the prim path is a regex pattern,
            then the asset is spawned at all the matching prim paths.
        cfg: The configuration instance.
        translation: The translation to apply to the prim w.r.t. its parent prim. Defaults to None.
        orientation: The orientation in (w, x, y, z) to apply to the prim w.r.t. its parent prim. Defaults to None.
        scale: The scale of the imported prim. Defaults to None.

    Returns:
        The prim of the spawned asset.
    """
    # -- spawn asset if it doesn't exist.
    if not prim_utils.is_prim_path_valid(prim_path):
        # urdf loader
        urdf_loader = loaders.UrdfLoader(cfg)
        # add prim as reference to stage
        prim_utils.create_prim(
            prim_path,
            usd_path=urdf_loader.usd_path,
            translation=translation,
            orientation=orientation,
            scale=scale,
        )
    else:
        carb.log_warn(f"A prim already exists at prim path: '{prim_path}'. Skipping...")

    # modify rigid body properties
    if cfg.rigid_props is not None:
        schemas.modify_rigid_body_properties(prim_path, cfg.rigid_props)
    # modify collision properties
    if cfg.collision_props is not None:
        schemas.modify_collision_properties(prim_path, cfg.collision_props)
    # modify articulation root properties
    if cfg.articulation_props is not None:
        schemas.modify_articulation_root_properties(prim_path, cfg.articulation_props)
    # return the prim
    return prim_utils.get_prim_at_path(prim_path)


def spawn_ground_plane(prim_path: str, cfg: from_files_cfg.GroundPlaneCfg, **kwargs) -> Usd.Prim:
    """Spawns a ground plane into the scene.

    This function loads the USD file containing the grid plane asset from Isaac Sim. It may
    not work with other assets for ground planes. In those cases, please use the `spawn_from_usd`
    function.

    Note:
        This function takes keyword arguments to be compatible with other spawners. However, it does not
        use any of the kwargs.

    Args:
        prim_path: The path to spawn the asset at.
        cfg: The configuration instance.

    Returns:
        The prim of the spawned asset.

    Raises:
        ValueError: If the prim path already exists.
    """
    # Spawn Ground-plane
    if not prim_utils.is_prim_path_valid(prim_path):
        prim_utils.create_prim(prim_path, usd_path=cfg.usd_path, translation=(0.0, 0.0, cfg.height))
    else:
        raise ValueError(f"A prim already exists at path: '{prim_path}'.")

    # Create physics material
    if cfg.physics_material is not None:
        cfg.physics_material.func(f"{prim_path}/physicsMaterial", cfg.physics_material)
        # Apply physics material to ground plane
        collision_prim_path = prim_utils.get_prim_path(
            prim_utils.get_first_matching_child_prim(
                prim_path, predicate=lambda x: prim_utils.get_prim_type_name(x) == "Plane"
            )
        )
        bind_physics_material(collision_prim_path, f"{prim_path}/physicsMaterial")

    # Scale only the mesh
    # Warning: This is specific to the default grid plane asset.
    if prim_utils.is_prim_path_valid(f"{prim_path}/Enviroment"):
        # compute scale from size
        scale = (cfg.size[0] / 100.0, cfg.size[1] / 100.0, 1.0)
        # apply scale to the mesh
        omni.kit.commands.execute(
            "ChangeProperty",
            prop_path=Sdf.Path(f"{prim_path}/Enviroment.xformOp:scale"),
            value=scale,
            prev=None,
        )

    # Change the color of the plane
    # Warning: This is specific to the default grid plane asset.
    if cfg.color is not None:
        omni.kit.commands.execute(
            "ChangePropertyCommand",
            prop_path=Sdf.Path(f"{prim_path}/Looks/theGrid.inputs:diffuse_tint"),
            value=Gf.Vec3d(*cfg.color),
            prev=None,
            type_to_create_if_not_exist=Sdf.ValueTypeNames.Color3f,
        )

    # return the prim
    return prim_utils.get_prim_at_path(prim_path)