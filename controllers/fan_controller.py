"""Automatic fan controller based on sensor readings."""

import numpy as np
from utils.constants import (
    KP, KI, KD, FAN_MIN_RUN_TIME, FAN_IDLE_THRESHOLD_PPM,
    PPM_GOOD, PPM_MODERATE, PPM_UNHEALTHY, AQI_FAN_SPEED_LEVELS
)


class FanController:
    """Automatic fan controller using sensor feedback."""
    
    def __init__(self, fan):
        """Initialize fan controller.
        
        Args:
            fan: ExhaustFan object to control
        """
        self.fan = fan
        self.mode = 'manual'  # 'manual' or 'auto'
        
        # Sensor pairs to monitor
        self.sensor_pairs = []
        
        # PID controller state
        self.integral_error = 0.0
        self.previous_error = 0.0
        self.target_ppm = PPM_GOOD  # Target air quality
        
        # Control logic state
        self.time_since_check = 0.0
        self.check_interval = 5.0  # Check every 5 seconds
        self.min_run_time = FAN_MIN_RUN_TIME
        
        # History
        self.control_history = []
        
    def set_mode(self, mode):
        """Set controller mode.
        
        Args:
            mode: 'manual' or 'auto'
        """
        if mode in ['manual', 'auto']:
            self.mode = mode
            if mode == 'auto':
                self.reset_pid()
    
    def add_sensor_pair(self, sensor_pair):
        """Add a sensor pair to monitor.
        
        Args:
            sensor_pair: SensorPair object
        """
        self.sensor_pairs.append(sensor_pair)
    
    def remove_sensor_pair(self, pair_id):
        """Remove a sensor pair.
        
        Args:
            pair_id: ID of sensor pair to remove
        """
        self.sensor_pairs = [sp for sp in self.sensor_pairs if sp.pair_id != pair_id]
    
    def clear_sensor_pairs(self):
        """Remove all sensor pairs."""
        self.sensor_pairs = []
    
    def reset_pid(self):
        """Reset PID controller state."""
        self.integral_error = 0.0
        self.previous_error = 0.0
    
    def update(self, dt):
        """Update controller (call every simulation step).
        
        Args:
            dt: Time step in seconds
        """
        if self.mode != 'auto' or len(self.sensor_pairs) == 0:
            return
        
        self.time_since_check += dt
        
        # Check sensors at intervals
        if self.time_since_check < self.check_interval:
            return
        
        self.time_since_check = 0.0
        
        # Get readings from all sensors
        low_readings = []
        high_readings = []
        
        for pair in self.sensor_pairs:
            readings = pair.get_readings()
            low_readings.append(readings['low'])
            high_readings.append(readings['high'])
        
        # Determine control action
        self._determine_fan_speed(low_readings, high_readings)
    
    def _determine_fan_speed(self, low_readings, high_readings):
        """Determine required fan speed based on sensor readings.
        
        Args:
            low_readings: List of low sensor readings
            high_readings: List of high sensor readings
        """
        # Strategy:
        # 1. Low sensors determine if air quality is acceptable at breathing level
        # 2. High sensors detect smoke accumulation near ceiling
        # 3. Use worst-case reading to determine fan speed
        
        # Find worst PPM readings
        low_ppms = [r['ppm'] for r in low_readings]
        high_ppms = [r['ppm'] for r in high_readings]
        
        max_low_ppm = max(low_ppms) if low_ppms else 0
        max_high_ppm = max(high_ppms) if high_ppms else 0
        
        # Use high sensor for speed determination (ceiling smoke)
        control_ppm = max_high_ppm
        
        # Use low sensor for timing/stopping (breathing level)
        check_ppm = max_low_ppm
        
        # Determine if we should run fan
        if check_ppm < FAN_IDLE_THRESHOLD_PPM and self.fan.run_time > self.min_run_time:
            # Air is clean enough, can turn off
            target_speed = 0.0
        else:
            # Need to run fan, determine speed based on PPM levels
            if control_ppm < PPM_GOOD:
                # Low smoke, minimal fan speed
                target_speed = 20.0
            elif control_ppm < PPM_MODERATE:
                # Moderate smoke, medium fan speed
                target_speed = 40.0
            elif control_ppm < PPM_UNHEALTHY:
                # High smoke, high fan speed
                target_speed = 70.0
            else:
                # Very high smoke, maximum fan speed
                target_speed = 100.0
            
            # Fine-tune with PID controller
            error = control_ppm - self.target_ppm
            self.integral_error += error * self.check_interval
            derivative_error = (error - self.previous_error) / self.check_interval
            
            pid_adjustment = (KP * error + 
                            KI * self.integral_error + 
                            KD * derivative_error)
            
            target_speed += pid_adjustment
            target_speed = np.clip(target_speed, 0.0, 100.0)
            
            self.previous_error = error
        
        # Set fan speed
        self.fan.set_speed(target_speed)
        
        # Log control action
        self.control_history.append({
            'time': self.fan.run_time,
            'max_low_ppm': max_low_ppm,
            'max_high_ppm': max_high_ppm,
            'target_speed': target_speed,
            'actual_speed': self.fan.speed_percent
        })
    
    def get_status(self):
        """Get controller status.
        
        Returns:
            Dictionary with controller status
        """
        return {
            'mode': self.mode,
            'num_sensors': len(self.sensor_pairs),
            'target_ppm': self.target_ppm,
            'integral_error': self.integral_error,
            'check_interval': self.check_interval
        }


class TripController:
    """Trip-based fan controller for sensor pair activation."""
    
    def __init__(self, fan):
        """Initialize trip controller.
        
        Args:
            fan: ExhaustFan object to control
        """
        self.fan = fan
        self.mode = 'manual'  # 'manual' or 'trip'
        
        # Sensor pairs to monitor
        self.sensor_pairs = []
        
        # Current simulation time
        self.current_time = 0.0
        
        # Control state
        self.any_sensor_tripped = False
        self.max_remaining_duration = 0.0
        self.highest_aqi = 0.0
        
        # History
        self.trip_history = []
    
    def set_mode(self, mode):
        """Set controller mode.
        
        Args:
            mode: 'manual' or 'trip'
        """
        if mode in ['manual', 'trip']:
            self.mode = mode
    
    def add_sensor_pair(self, sensor_pair):
        """Add a sensor pair to monitor.
        
        Args:
            sensor_pair: SensorPair object
        """
        self.sensor_pairs.append(sensor_pair)
    
    def remove_sensor_pair(self, pair_id):
        """Remove a sensor pair.
        
        Args:
            pair_id: ID of sensor pair to remove
        """
        self.sensor_pairs = [sp for sp in self.sensor_pairs if sp.pair_id != pair_id]
    
    def clear_sensor_pairs(self):
        """Remove all sensor pairs."""
        self.sensor_pairs = []
    
    def calculate_fan_speed_from_aqi(self, aqi):
        """Calculate target fan speed based on AQI level.
        
        Args:
            aqi: Air Quality Index value (0-500)
            
        Returns:
            Target fan speed percentage (0-100)
        """
        # Use AQI-based speed levels from constants
        for aqi_low, aqi_high, speed in AQI_FAN_SPEED_LEVELS:
            if aqi_low <= aqi <= aqi_high:
                return float(speed)
        
        # If AQI is above all levels, return max speed
        if aqi > AQI_FAN_SPEED_LEVELS[-1][1]:
            return 100.0
        
        # If AQI is below all levels (shouldn't happen), return min speed
        return 0.0
    
    def update(self, dt):
        """Update controller (call every simulation step).
        
        Args:
            dt: Time step in seconds
        """
        if self.mode != 'trip' or len(self.sensor_pairs) == 0:
            return
        
        self.current_time += dt
        
        # Update all sensor pairs and check trip conditions
        tripped_sensors = []
        max_duration = 0.0
        max_aqi = 0.0
        
        for pair in self.sensor_pairs:
            # Update trip state for this sensor pair
            is_tripped = pair.update_trip_state(self.current_time, dt)
            
            if is_tripped:
                tripped_sensors.append(pair)
                
                # Track maximum remaining duration (Option D: use longest duration)
                if pair.remaining_duration > max_duration:
                    max_duration = pair.remaining_duration
                
                # Track highest AQI for fan speed calculation
                pair_aqi = pair.get_max_aqi()
                if pair_aqi > max_aqi:
                    max_aqi = pair_aqi
        
        # Update controller state
        self.any_sensor_tripped = len(tripped_sensors) > 0
        self.max_remaining_duration = max_duration
        self.highest_aqi = max_aqi
        
        # Determine fan speed
        if self.any_sensor_tripped:
            # At least one sensor is tripped, calculate fan speed from highest AQI
            target_speed = self.calculate_fan_speed_from_aqi(self.highest_aqi)
        else:
            # No sensors tripped, turn off fan
            target_speed = 0.0
        
        # Set fan speed
        self.fan.set_speed(target_speed)
        
        # Log control action
        self.trip_history.append({
            'time': self.current_time,
            'num_tripped': len(tripped_sensors),
            'max_duration': max_duration,
            'highest_aqi': max_aqi,
            'target_speed': target_speed,
            'actual_speed': self.fan.speed_percent
        })
    
    def get_status(self):
        """Get controller status.
        
        Returns:
            Dictionary with controller status
        """
        # Get status of each sensor pair
        sensor_statuses = []
        for pair in self.sensor_pairs:
            sensor_statuses.append({
                'pair_id': pair.pair_id,
                'is_tripped': pair.is_tripped,
                'remaining_duration': pair.remaining_duration,
                'trip_ppm': pair.trip_ppm,
                'trip_aqi': pair.trip_aqi,
                'trip_duration': pair.trip_duration
            })
        
        return {
            'mode': self.mode,
            'num_sensors': len(self.sensor_pairs),
            'any_sensor_tripped': self.any_sensor_tripped,
            'max_remaining_duration': self.max_remaining_duration,
            'highest_aqi': self.highest_aqi,
            'sensor_statuses': sensor_statuses
        }
    
    def reset(self):
        """Reset controller state."""
        self.current_time = 0.0
        self.any_sensor_tripped = False
        self.max_remaining_duration = 0.0
        self.highest_aqi = 0.0
        self.trip_history = []
        
        # Reset all sensor pairs
        for pair in self.sensor_pairs:
            pair.reset()
