"""Data logging and CSV export functionality."""

import csv
import os
from datetime import datetime
import numpy as np
from collections import deque
from utils.constants import DATA_LOG_INTERVAL, MAX_GRAPH_POINTS, DATA_EXPORT_DIR


class DataLogger:
    """Logs simulation data for analysis and export."""
    
    def __init__(self):
        """Initialize data logger."""
        self.time_data = deque(maxlen=MAX_GRAPH_POINTS)
        self.fan_speed_data = deque(maxlen=MAX_GRAPH_POINTS)
        self.room_ppm_data = deque(maxlen=MAX_GRAPH_POINTS)
        self.room_clarity_data = deque(maxlen=MAX_GRAPH_POINTS)
        
        # Sensor data (keyed by sensor ID)
        self.sensor_ppm_data = {}
        self.sensor_clarity_data = {}
        
        # Statistics
        self.peak_ppm = 0.0
        self.avg_ppm = 0.0
        self.time_to_clear = None
        self.clearance_threshold = 50.0  # PPM
        
        # Logging control
        self.time_since_log = 0.0
        self.log_interval = DATA_LOG_INTERVAL
        
        # Full data for export (not limited)
        self.full_data = []
        
    def update(self, simulation_time, fan, smoke_sim, sensor_pairs, dt):
        """Update data logger with current state.
        
        Args:
            simulation_time: Current simulation time
            fan: ExhaustFan object
            smoke_sim: SmokeSimulation object
            sensor_pairs: List of SensorPair objects
            dt: Time step
        """
        self.time_since_log += dt
        
        if self.time_since_log < self.log_interval:
            return
        
        self.time_since_log = 0.0
        
        # Get current values
        room_ppm = smoke_sim.calculate_room_average_ppm()
        room_clarity = smoke_sim.calculate_room_average_clarity()
        fan_speed = fan.speed_percent
        
        # Update time series
        self.time_data.append(simulation_time)
        self.fan_speed_data.append(fan_speed)
        self.room_ppm_data.append(room_ppm)
        self.room_clarity_data.append(room_clarity)
        
        # Update statistics
        if room_ppm > self.peak_ppm:
            self.peak_ppm = room_ppm
        
        # Calculate average PPM
        if len(self.room_ppm_data) > 0:
            self.avg_ppm = np.mean(self.room_ppm_data)
        
        # Check if room has cleared
        if self.time_to_clear is None and room_ppm < self.clearance_threshold:
            if len(self.room_ppm_data) > 10:  # Must be stable
                recent_ppms = list(self.room_ppm_data)[-10:]
                if all(ppm < self.clearance_threshold for ppm in recent_ppms):
                    self.time_to_clear = simulation_time
        
        # Log sensor data
        data_point = {
            'time': simulation_time,
            'fan_speed': fan_speed,
            'room_ppm': room_ppm,
            'room_clarity': room_clarity,
            'particle_count': smoke_sim.get_particle_count()
        }
        
        for pair in sensor_pairs:
            readings = pair.get_readings()
            low_reading = readings['low']
            high_reading = readings['high']
            
            low_id = low_reading['id']
            high_id = high_reading['id']
            
            # Initialize if new sensor
            if low_id not in self.sensor_ppm_data:
                self.sensor_ppm_data[low_id] = deque(maxlen=MAX_GRAPH_POINTS)
                self.sensor_clarity_data[low_id] = deque(maxlen=MAX_GRAPH_POINTS)
            
            if high_id not in self.sensor_ppm_data:
                self.sensor_ppm_data[high_id] = deque(maxlen=MAX_GRAPH_POINTS)
                self.sensor_clarity_data[high_id] = deque(maxlen=MAX_GRAPH_POINTS)
            
            # Append data
            self.sensor_ppm_data[low_id].append(low_reading['ppm'])
            self.sensor_clarity_data[low_id].append(low_reading['clarity_percent'])
            self.sensor_ppm_data[high_id].append(high_reading['ppm'])
            self.sensor_clarity_data[high_id].append(high_reading['clarity_percent'])
            
            # Add to data point
            data_point[f'{low_id}_ppm'] = low_reading['ppm']
            data_point[f'{low_id}_clarity'] = low_reading['clarity_percent']
            data_point[f'{high_id}_ppm'] = high_reading['ppm']
            data_point[f'{high_id}_clarity'] = high_reading['clarity_percent']
        
        self.full_data.append(data_point)
    
    def export_to_csv(self, filename=None):
        """Export data to CSV file.
        
        Args:
            filename: Output filename (optional, auto-generated if not provided)
            
        Returns:
            Path to exported file
        """
        # Create export directory if it doesn't exist
        os.makedirs(DATA_EXPORT_DIR, exist_ok=True)
        
        # Generate filename if not provided
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"smoke_sim_data_{timestamp}.csv"
        
        filepath = os.path.join(DATA_EXPORT_DIR, filename)
        
        # Write data
        if len(self.full_data) == 0:
            return None
        
        keys = self.full_data[0].keys()
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(self.full_data)
        
        return filepath
    
    def get_statistics(self):
        """Get statistical summary.
        
        Returns:
            Dictionary with statistics
        """
        return {
            'peak_ppm': self.peak_ppm,
            'average_ppm': self.avg_ppm,
            'time_to_clear': self.time_to_clear,
            'current_room_ppm': self.room_ppm_data[-1] if self.room_ppm_data else 0,
            'current_room_clarity': self.room_clarity_data[-1] if self.room_clarity_data else 100,
            'data_points': len(self.full_data)
        }
    
    def get_graph_data(self):
        """Get data for real-time graphs.
        
        Returns:
            Dictionary with time series data
        """
        return {
            'time': list(self.time_data),
            'fan_speed': list(self.fan_speed_data),
            'room_ppm': list(self.room_ppm_data),
            'room_clarity': list(self.room_clarity_data),
            'sensor_ppm': {k: list(v) for k, v in self.sensor_ppm_data.items()},
            'sensor_clarity': {k: list(v) for k, v in self.sensor_clarity_data.items()}
        }
    
    def reset(self):
        """Reset all logged data."""
        self.time_data.clear()
        self.fan_speed_data.clear()
        self.room_ppm_data.clear()
        self.room_clarity_data.clear()
        self.sensor_ppm_data.clear()
        self.sensor_clarity_data.clear()
        self.full_data.clear()
        
        self.peak_ppm = 0.0
        self.avg_ppm = 0.0
        self.time_to_clear = None
        self.time_since_log = 0.0
