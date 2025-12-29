"""Configuration save/load management."""

import json
import os
from utils.constants import CONFIG_DIR, DEFAULT_CONFIG_FILE


class ConfigManager:
    """Manages saving and loading of simulation configurations."""
    
    def __init__(self):
        """Initialize config manager."""
        # Create config directory if it doesn't exist
        os.makedirs(CONFIG_DIR, exist_ok=True)
        
    def save_config(self, config_data, filename=None):
        """Save configuration to JSON file.
        
        Args:
            config_data: Dictionary with configuration
            filename: Output filename (optional)
            
        Returns:
            Path to saved config file
        """
        if filename is None:
            filename = DEFAULT_CONFIG_FILE
        
        filepath = os.path.join(CONFIG_DIR, filename)
        
        with open(filepath, 'w') as f:
            json.dump(config_data, f, indent=2)
        
        return filepath
    
    def load_config(self, filename=None):
        """Load configuration from JSON file.
        
        Args:
            filename: Config filename (optional, uses default if not provided)
            
        Returns:
            Dictionary with configuration, or None if file doesn't exist
        """
        if filename is None:
            filename = DEFAULT_CONFIG_FILE
        
        filepath = os.path.join(CONFIG_DIR, filename)
        
        if not os.path.exists(filepath):
            return None
        
        with open(filepath, 'r') as f:
            config_data = json.load(f)
        
        return config_data
    
    def list_configs(self):
        """List all available config files.
        
        Returns:
            List of config filenames
        """
        if not os.path.exists(CONFIG_DIR):
            return []
        
        files = os.listdir(CONFIG_DIR)
        return [f for f in files if f.endswith('.json')]
    
    def delete_config(self, filename):
        """Delete a config file.
        
        Args:
            filename: Config filename to delete
            
        Returns:
            True if deleted, False if file didn't exist
        """
        filepath = os.path.join(CONFIG_DIR, filename)
        
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
        
        return False
    
    @staticmethod
    def create_config_dict(sensor_pairs, num_smokers, fan_mode, simulation_speed):
        """Create configuration dictionary from current state.
        
        Args:
            sensor_pairs: List of SensorPair objects
            num_smokers: Number of active smokers
            fan_mode: 'manual', 'auto', or 'trip'
            simulation_speed: Simulation speed multiplier
            
        Returns:
            Configuration dictionary
        """
        sensors_config = []
        for pair in sensor_pairs:
            sensors_config.append({
                'pair_id': pair.pair_id,
                'distance_from_fan': pair.distance_from_fan,
                'low_height': pair.low_height,
                'high_height': pair.high_height,
                'wall': pair.wall,
                # Trip control settings
                'trip_ppm': pair.trip_ppm,
                'trip_aqi': pair.trip_aqi,
                'trip_duration': pair.trip_duration
            })
        
        config = {
            'sensors': sensors_config,
            'simulation': {
                'num_smokers': num_smokers,
                'fan_mode': fan_mode,
                'simulation_speed': simulation_speed
            }
        }
        
        return config
