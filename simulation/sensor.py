"""Sensor models for air quality monitoring."""

import numpy as np
from collections import deque
from utils.constants import (
    SENSOR_DETECTION_RADIUS, SENSOR_RESPONSE_TIME, SENSOR_MIN_HEIGHT,
    SENSOR_MAX_HEIGHT, EXTINCTION_COEFFICIENT, ROOM_WIDTH, ROOM_LENGTH,
    PPM_TO_UG_M3, AQI_BREAKPOINTS, DEFAULT_TRIP_PPM, DEFAULT_TRIP_AQI,
    DEFAULT_TRIP_DURATION
)


class Sensor:
    """Represents an air quality sensor."""
    
    @staticmethod
    def calculate_aqi_from_concentration(concentration_ug_m3):
        """Calculate AQI from PM2.5 concentration using EPA formula.
        
        Args:
            concentration_ug_m3: PM2.5 concentration in µg/m³
            
        Returns:
            AQI value (0-500)
        """
        # Find the appropriate breakpoint
        for aqi_low, aqi_high, conc_low, conc_high in AQI_BREAKPOINTS:
            if conc_low <= concentration_ug_m3 <= conc_high:
                # Linear interpolation formula
                # AQI = ((AQI_high - AQI_low) / (Conc_high - Conc_low)) * (Conc - Conc_low) + AQI_low
                aqi = ((aqi_high - aqi_low) / (conc_high - conc_low)) * (concentration_ug_m3 - conc_low) + aqi_low
                return np.clip(aqi, 0, 500)
        
        # If concentration exceeds all breakpoints, return max AQI
        if concentration_ug_m3 > AQI_BREAKPOINTS[-1][3]:
            return 500.0
        
        return 0.0
    
    @staticmethod
    def ppm_to_aqi(ppm):
        """Convert PPM to AQI.
        
        Args:
            ppm: Parts per million reading
            
        Returns:
            AQI value (0-500)
        """
        # Convert PPM to µg/m³
        concentration_ug_m3 = ppm * PPM_TO_UG_M3
        
        # Calculate AQI
        return Sensor.calculate_aqi_from_concentration(concentration_ug_m3)
    
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
        self.aqi = 0.0
        
        # Reading history for smoothing (simulate response time)
        self.ppm_history = deque(maxlen=10)
        self.clarity_history = deque(maxlen=10)
        self.aqi_history = deque(maxlen=10)
        
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
        
        # Calculate AQI from PPM
        instantaneous_aqi = self.ppm_to_aqi(self.ppm)
        self.aqi_history.append(instantaneous_aqi)
        
        # Smooth AQI reading
        if len(self.aqi_history) > 0:
            self.aqi = np.mean(self.aqi_history)
        
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
            Dictionary with PPM, AQI, and clarity readings
        """
        return {
            'id': self.id,
            'type': self.type,
            'position': self.position.tolist(),
            'ppm': self.ppm,
            'aqi': self.aqi,
            'clarity_percent': self.clarity_percent
        }
    
    def reset(self):
        """Reset sensor readings."""
        self.ppm = 0.0
        self.clarity_percent = 100.0
        self.aqi = 0.0
        self.ppm_history.clear()
        self.clarity_history.clear()
        self.aqi_history.clear()
        self.time_since_update = 0.0


class SensorPair:
    """Represents a pair of low and high sensors."""
    
    def __init__(self, pair_id, distance_from_fan, low_height, high_height, fan_position, wall='south',
                 trip_ppm=None, trip_aqi=None, trip_duration=None):
        """Initialize sensor pair.
        
        Args:
            pair_id: Unique identifier for the pair
            distance_from_fan: Distance from fan entrance (feet)
            low_height: Height of low sensor from floor (feet)
            high_height: Height of high sensor from floor (feet)
            fan_position: Position of the fan (numpy array)
            wall: Which wall to place sensors on ('north' or 'south')
            trip_ppm: PPM threshold for trip activation (default: DEFAULT_TRIP_PPM)
            trip_aqi: AQI threshold for trip activation (default: DEFAULT_TRIP_AQI)
            trip_duration: Duration in seconds for fan to run after trip (default: DEFAULT_TRIP_DURATION)
        """
        self.pair_id = pair_id
        self.distance_from_fan = distance_from_fan
        self.low_height = np.clip(low_height, SENSOR_MIN_HEIGHT, SENSOR_MAX_HEIGHT)
        self.high_height = np.clip(high_height, SENSOR_MIN_HEIGHT, SENSOR_MAX_HEIGHT)
        self.wall = wall
        
        # Trip control settings
        self.trip_ppm = trip_ppm if trip_ppm is not None else DEFAULT_TRIP_PPM
        self.trip_aqi = trip_aqi if trip_aqi is not None else DEFAULT_TRIP_AQI
        self.trip_duration = trip_duration if trip_duration is not None else DEFAULT_TRIP_DURATION
        
        # Trip state tracking
        self.is_tripped = False
        self.trip_start_time = None
        self.remaining_duration = 0.0
        
        # Calculate sensor positions
        fan_x, fan_y, fan_z = fan_position
        
        # Place sensors based on distance_from_fan parameter
        # Sensors are positioned along the Z-axis (length of room) from the fan
        sensor_z = fan_z + distance_from_fan
        sensor_z = np.clip(sensor_z, 0, ROOM_LENGTH)
        
        # Calculate X position based on wall selection
        if wall.lower() == 'north':
            sensor_x = 0.5  # 6 inches from North wall (x≈0)
        else:  # south wall (default)
            sensor_x = 29.5  # 6 inches from South wall (ROOM_WIDTH=30, so 30-0.5=29.5)
        
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
        """Reset both sensors and trip state."""
        self.low_sensor.reset()
        self.high_sensor.reset()
        self.is_tripped = False
        self.trip_start_time = None
        self.remaining_duration = 0.0
    
    def check_trip_condition(self):
        """Check if sensor pair should trip based on current readings.
        
        Returns:
            Boolean indicating if trip condition is met
        """
        # Get readings from both sensors
        low_reading = self.low_sensor.get_reading()
        high_reading = self.high_sensor.get_reading()
        
        # Check if either sensor exceeds thresholds
        # Use the higher reading from the two sensors
        max_ppm = max(low_reading['ppm'], high_reading['ppm'])
        max_aqi = max(low_reading['aqi'], high_reading['aqi'])
        
        # Trip if PPM OR AQI exceeds threshold
        return max_ppm > self.trip_ppm or max_aqi > self.trip_aqi
    
    def update_trip_state(self, current_time, dt):
        """Update trip state based on current readings and time.
        
        Args:
            current_time: Current simulation time in seconds
            dt: Time step in seconds
            
        Returns:
            Boolean indicating if sensor is currently tripped
        """
        # Check if trip condition is met
        if self.check_trip_condition():
            if not self.is_tripped:
                # New trip activation
                self.is_tripped = True
                self.trip_start_time = current_time
                self.remaining_duration = self.trip_duration
            else:
                # Trip condition still active, reset duration
                self.remaining_duration = self.trip_duration
        else:
            # Trip condition not met, countdown remaining duration
            if self.is_tripped and self.remaining_duration > 0:
                self.remaining_duration -= dt
                
                # Check if trip duration has expired
                if self.remaining_duration <= 0:
                    self.is_tripped = False
                    self.trip_start_time = None
                    self.remaining_duration = 0.0
        
        return self.is_tripped
    
    def get_max_aqi(self):
        """Get the maximum AQI from both sensors.
        
        Returns:
            Maximum AQI value
        """
        low_reading = self.low_sensor.get_reading()
        high_reading = self.high_sensor.get_reading()
        return max(low_reading['aqi'], high_reading['aqi'])
