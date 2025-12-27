"""Automatic fan controller based on sensor readings."""

import numpy as np
from utils.constants import (
    KP, KI, KD, FAN_MIN_RUN_TIME, FAN_IDLE_THRESHOLD_PPM,
    PPM_GOOD, PPM_MODERATE, PPM_UNHEALTHY
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
