"""
Kinematics module for Tragictory Physics.

This module contains physics simulation models for projectile motion
and other kinematics calculations using numpy for efficient computations.
"""

import numpy as np
from typing import Tuple


class ProjectileModel:
    """Model for projectile motion calculations.
    
    Provides methods to calculate trajectory coordinates for projectiles
    under the influence of gravity using standard kinematics equations.
    """
    
    @staticmethod
    def calculate_trajectory(
        v0: float, 
        angle_deg: float, 
        gravity: float = 9.81
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Calculate projectile trajectory coordinates.
        
        Calculates the X and Y coordinates of a projectile from launch (t=0)
        until landing (y=0) using the kinematics equations:
        X(t) = v0 * cos(angle) * t
        Y(t) = v0 * sin(angle) * t - (g * t^2) / 2
        
        Args:
            v0: Initial velocity in m/s.
            angle_deg: Launch angle in degrees.
            gravity: Gravitational acceleration in m/s² (default: 9.81).
            
        Returns:
            Tuple[np.ndarray, np.ndarray]: Two numpy arrays containing
                x_coords and y_coords of the trajectory.
        """
        # Convert angle to radians
        angle_rad = np.radians(angle_deg)
        
        # Calculate velocity components
        v0_x = v0 * np.cos(angle_rad)
        v0_y = v0 * np.sin(angle_rad)
        
        # Calculate time of flight (when projectile returns to y=0)
        # Using quadratic formula: v0_y * t - (g * t^2) / 2 = 0
        # Solutions: t = 0 (launch) and t = 2 * v0_y / g (landing)
        if v0_y <= 0:
            # If angle is 0 or negative, projectile doesn't go up
            time_of_flight = 0.001  # Minimal time to avoid division by zero
        else:
            time_of_flight = 2 * v0_y / gravity
        
        # Generate time array from 0 to time_of_flight
        # Use 100 points for smooth trajectory
        time_points = np.linspace(0, time_of_flight, 100)
        
        # Calculate coordinates using kinematics equations
        x_coords = v0_x * time_points
        y_coords = v0_y * time_points - (gravity * time_points ** 2) / 2
        
        # Ensure y doesn't go below 0 (ground level)
        y_coords = np.maximum(y_coords, 0)
        
        return x_coords, y_coords
    
    @staticmethod
    def calculate_max_height(v0: float, angle_deg: float, gravity: float = 9.81) -> float:
        """Calculate maximum height of projectile.
        
        Args:
            v0: Initial velocity in m/s.
            angle_deg: Launch angle in degrees.
            gravity: Gravitational acceleration in m/s².
            
        Returns:
            float: Maximum height in meters.
        """
        angle_rad = np.radians(angle_deg)
        v0_y = v0 * np.sin(angle_rad)
        
        # Maximum height: h_max = (v0_y^2) / (2 * g)
        if v0_y <= 0:
            return 0.0
        
        return (v0_y ** 2) / (2 * gravity)
    
    @staticmethod
    def calculate_range(v0: float, angle_deg: float, gravity: float = 9.81) -> float:
        """Calculate horizontal range of projectile.
        
        Args:
            v0: Initial velocity in m/s.
            angle_deg: Launch angle in degrees.
            gravity: Gravitational acceleration in m/s².
            
        Returns:
            float: Horizontal range in meters.
        """
        angle_rad = np.radians(angle_deg)
        v0_y = v0 * np.sin(angle_rad)
        
        # Range: R = (v0^2 * sin(2*angle)) / g
        if v0_y <= 0:
            return 0.0
        
        return (v0 ** 2 * np.sin(2 * angle_rad)) / gravity
    
    @staticmethod
    def calculate_time_of_flight(v0: float, angle_deg: float, gravity: float = 9.81) -> float:
        """Calculate total time of flight.
        
        Args:
            v0: Initial velocity in m/s.
            angle_deg: Launch angle in degrees.
            gravity: Gravitational acceleration in m/s².
            
        Returns:
            float: Time of flight in seconds.
        """
        angle_rad = np.radians(angle_deg)
        v0_y = v0 * np.sin(angle_rad)
        
        # Time of flight: t = 2 * v0_y / g
        if v0_y <= 0:
            return 0.0
        
        return 2 * v0_y / gravity
