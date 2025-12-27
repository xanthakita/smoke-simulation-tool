"""Sensor models for air quality monitoring."""

import numpy as np
from collections import deque
from utils.constants import (
    SENSOR_DETECTION_RADIUS, SENSOR_RESPONSE_TIME, SENSOR_MIN_HEIGHT,
    SENSOR_MAX_HEIGHT, EXTINCTION_COEFFICIENT, ROOM_WIDTH, ROOM_LENGTH
)


class Sensor:
    """Represents an air quality sensor."""
    
    def __init__(self, sensor_id, position, sensor_type='low'):
        """Initialize sensor.
        
        Args:
            sensor_id: Unique identifier for the sensor
            position: numpy array [x, y, z] position in room
            sensor_type: 'low' or 'high' sensor
        """
        self.id = sensor_id
        self.position = np.array(position, dtype=float)
        self.type = sensor_type  # 'low' or 'high'
        self.detection_radius = SENSOR_DETECTION_RADIUS
        
        # Current readings
        self.ppm = 0.0
        self.clarity_percent = 100.0
        
        # Reading history for smoothing (simulate response time)
        self.ppm_history = deque(maxlen=10)
        self.clarity_history = deque(maxlen=10)
        
        # Response time simulation
        self.response_time = SENSOR_RESPONSE_TIME
        self.time_since_update = 0.0
        
    def update_reading(self, particles_positions, dt):
        """Update sensor readings based on nearby particles.
        
        Args:
            particles_positions: numpy array of particle positions
            dt: Time step in seconds
        """
        self.time_since_update += dt
        
        # Only update at intervals to simulate response time
        if self.time_since_update < self.response_time / 10:
            return
        
        self.time_since_update = 0.0
        
        # Count particles within detection radius
        if len(particles_positions) > 0:
            distances = np.linalg.norm(particles_positions - self.position, axis=1)
            particles_in_range = np.sum(distances <= self.detection_radius)
            
            # Calculate detection volume (sphere)
            detection_volume = (4.0 / 3.0) * np.pi * (self.detection_radius ** 3)
            
            # Convert to PPM (parts per million)
            # This is a simplified model: particles per cubic foot -> PPM
            particles_per_cubic_foot = particles_in_range / detection_volume if detection_volume > 0 else 0
            instantaneous_ppm = particles_per_cubic_foot * 10  # Scaling factor
        else:
            instantaneous_ppm = 0.0
        
        # Add to history for smoothing
        self.ppm_history.append(instantaneous_ppm)
        
        # Smooth reading (moving average)
        if len(self.ppm_history) > 0:
            self.ppm = np.mean(self.ppm_history)
        
        # Calculate air clarity using Beer-Lambert law
        # I/I0 = e^(-alpha * c * d)
        # where c is concentration (PPM), d is path length
        path_length = 10.0  # Assume 10 feet visibility distance
        self.clarity_percent = 100.0 * np.exp(-EXTINCTION_COEFFICIENT * self.ppm * path_length)
        self.clarity_percent = np.clip(self.clarity_percent, 0.0, 100.0)
        
        self.clarity_history.append(self.clarity_percent)
        if len(self.clarity_history) > 0:
            self.clarity_percent = np.mean(self.clarity_history)
    
    def get_reading(self):
        """Get current sensor readings.
        
        Returns:
            Dictionary with PPM and clarity readings
        """
        return {
            'id': self.id,
            'type': self.type,
            'position': self.position.tolist(),
            'ppm': self.ppm,
            'clarity_percent': self.clarity_percent
        }
    
    def reset(self):
        """Reset sensor readings."""
        self.ppm = 0.0
        self.clarity_percent = 100.0
        self.ppm_history.clear()
        self.clarity_history.clear()
        self.time_since_update = 0.0


class SensorPair:
    """Represents a pair of low and high sensors."""
    
    def __init__(self, pair_id, distance_from_fan, low_height, high_height, fan_position):
        """Initialize sensor pair.
        
        Args:
            pair_id: Unique identifier for the pair
            distance_from_fan: Distance from fan entrance (feet)
            low_height: Height of low sensor from floor (feet)
            high_height: Height of high sensor from floor (feet)
            fan_position: Position of the fan (numpy array)
        """
        self.pair_id = pair_id
        self.distance_from_fan = distance_from_fan
        self.low_height = np.clip(low_height, SENSOR_MIN_HEIGHT, SENSOR_MAX_HEIGHT)
        self.high_height = np.clip(high_height, SENSOR_MIN_HEIGHT, SENSOR_MAX_HEIGHT)
        
        # Calculate sensor positions
        # Fan is on back wall, sensors are placed along Z-axis toward front
        fan_x, fan_y, fan_z = fan_position
        
        # Place sensors at same X position as fan, but closer to front
        sensor_x = fan_x
        sensor_z = fan_z - distance_from_fan
        sensor_z = np.clip(sensor_z, 0, ROOM_LENGTH)
        
        low_pos = np.array([sensor_x, self.low_height, sensor_z])
        high_pos = np.array([sensor_x, self.high_height, sensor_z])
        
        # Create sensors
        self.low_sensor = Sensor(f"{pair_id}_low", low_pos, 'low')
        self.high_sensor = Sensor(f"{pair_id}_high", high_pos, 'high')
    
    def update(self, particle_positions, dt):
        """Update both sensors in the pair.
        
        Args:
            particle_positions: numpy array of particle positions
            dt: Time step in seconds
        """
        self.low_sensor.update_reading(particle_positions, dt)
        self.high_sensor.update_reading(particle_positions, dt)
    
    def get_readings(self):
        """Get readings from both sensors.
        
        Returns:
            Dictionary with low and high sensor readings
        """
        return {
            'pair_id': self.pair_id,
            'low': self.low_sensor.get_reading(),
            'high': self.high_sensor.get_reading()
        }
    
    def reset(self):
        """Reset both sensors."""
        self.low_sensor.reset()
        self.high_sensor.reset()
