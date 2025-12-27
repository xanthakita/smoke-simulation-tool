"""Exhaust fan model and control."""

import numpy as np
from utils.constants import (
    FAN_POSITION, FAN_DIAMETER, FAN_RADIUS, FAN_MIN_SPEED, FAN_MAX_SPEED,
    FAN_MAX_CFM, FAN_MAX_VELOCITY, FAN_RAMP_RATE, TIME_STEP
)


class ExhaustFan:
    """Represents the exhaust fan in the room."""
    
    def __init__(self):
        """Initialize the exhaust fan."""
        self.position = FAN_POSITION.copy()
        self.diameter = FAN_DIAMETER
        self.radius = FAN_RADIUS
        self.area = np.pi * self.radius ** 2
        
        # Fan state
        self.speed_percent = 0.0  # Current speed (0-100%)
        self.target_speed_percent = 0.0  # Target speed for ramping
        self.is_running = False
        self.run_time = 0.0  # Total time fan has been running
        
        # Performance characteristics
        self.max_cfm = FAN_MAX_CFM
        self.max_velocity = FAN_MAX_VELOCITY
        
        # Control parameters
        self.ramp_rate = FAN_RAMP_RATE  # Percent per second
        
    def set_speed(self, speed_percent):
        """Set target fan speed.
        
        Args:
            speed_percent: Speed in percentage (0-100)
        """
        self.target_speed_percent = np.clip(speed_percent, FAN_MIN_SPEED, FAN_MAX_SPEED)
        
        if self.target_speed_percent > 0:
            self.is_running = True
        else:
            self.is_running = False
    
    def update(self, dt):
        """Update fan state (handle ramping).
        
        Args:
            dt: Time step in seconds
        """
        if self.is_running:
            self.run_time += dt
        
        # Ramp speed toward target
        if abs(self.speed_percent - self.target_speed_percent) > 0.1:
            if self.speed_percent < self.target_speed_percent:
                self.speed_percent += self.ramp_rate * dt
                self.speed_percent = min(self.speed_percent, self.target_speed_percent)
            else:
                self.speed_percent -= self.ramp_rate * dt
                self.speed_percent = max(self.speed_percent, self.target_speed_percent)
        else:
            self.speed_percent = self.target_speed_percent
    
    def get_current_cfm(self):
        """Get current CFM based on speed.
        
        Returns:
            Current airflow in cubic feet per minute
        """
        return self.max_cfm * (self.speed_percent / 100.0)
    
    def get_current_velocity(self):
        """Get current air velocity at fan face.
        
        Returns:
            Velocity in feet per second
        """
        return self.max_velocity * (self.speed_percent / 100.0)
    
    def calculate_velocity_field(self, positions):
        """Calculate velocity field at given positions due to fan suction.
        
        Args:
            positions: numpy array of shape (N, 3) with particle positions
            
        Returns:
            numpy array of shape (N, 3) with velocity vectors
        """
        if self.speed_percent <= 0:
            return np.zeros_like(positions)
        
        # Vector from particle to fan center
        to_fan = self.position - positions
        distances = np.linalg.norm(to_fan, axis=1, keepdims=True)
        
        # Avoid division by zero
        distances = np.maximum(distances, 0.1)
        
        # Direction vectors (normalized)
        directions = to_fan / distances
        
        # Velocity magnitude using inverse square law with fan area
        # Stronger near fan, weaker far away
        current_velocity = self.get_current_velocity()
        
        # Modified to create more realistic flow pattern
        # Velocity falls off with distance but is strong near fan
        velocity_magnitudes = current_velocity * (self.area / (distances ** 1.5))
        velocity_magnitudes = np.clip(velocity_magnitudes, 0, current_velocity * 2)
        
        # Apply directional component
        velocities = directions * velocity_magnitudes
        
        return velocities
    
    def get_info(self):
        """Get fan information as dictionary.
        
        Returns:
            Dictionary with fan state information
        """
        return {
            'position': self.position.tolist(),
            'speed_percent': self.speed_percent,
            'target_speed': self.target_speed_percent,
            'is_running': self.is_running,
            'cfm': self.get_current_cfm(),
            'velocity': self.get_current_velocity(),
            'run_time': self.run_time
        }
    
    def reset(self):
        """Reset fan to initial state."""
        self.speed_percent = 0.0
        self.target_speed_percent = 0.0
        self.is_running = False
        self.run_time = 0.0
