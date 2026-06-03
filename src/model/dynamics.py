"""
Dynamics model module for Tragictory Physics.

This module contains physics models for dynamics simulations,
including the inclined plane model.
"""

import numpy as np


class InclinedPlaneModel:
    """Physics model for a block on an inclined plane.

    Calculates all forces acting on a block resting or sliding
    on a frictionless or frictional inclined surface.
    """

    @staticmethod
    def calculate_forces(
        mass: float,
        angle_deg: float,
        friction_coeff: float,
        gravity: float = 9.81
    ) -> dict:
        """Calculate forces acting on a block on an inclined plane.

        Args:
            mass: Mass of the block in kilograms (kg).
            angle_deg: Inclination angle of the plane in degrees.
            friction_coeff: Coefficient of static/kinetic friction (dimensionless).
            gravity: Gravitational acceleration in m/s². Defaults to 9.81.

        Returns:
            dict: A dictionary containing the following keys:
                - 'F_gravity' (float): Total gravitational force (N).
                - 'F_parallel' (float): Component of gravity along the slope (N).
                - 'F_normal' (float): Normal force perpendicular to the slope (N).
                - 'F_friction_max' (float): Maximum static friction force (N).
                - 'F_net' (float): Net force along the slope (N); 0 if block is at rest.
                - 'acceleration' (float): Resulting acceleration of the block (m/s²).
        """
        angle_rad: float = np.deg2rad(angle_deg)

        f_gravity: float = mass * gravity
        f_parallel: float = mass * gravity * np.sin(angle_rad)
        f_normal: float = mass * gravity * np.cos(angle_rad)
        f_friction_max: float = friction_coeff * f_normal

        # Net force is zero if friction can hold the block
        f_net: float = max(0.0, f_parallel - f_friction_max)
        acceleration: float = f_net / mass if mass > 0 else 0.0

        return {
            'F_gravity': float(f_gravity),
            'F_parallel': float(f_parallel),
            'F_normal': float(f_normal),
            'F_friction_max': float(f_friction_max),
            'F_net': float(f_net),
            'acceleration': float(acceleration),
        }
