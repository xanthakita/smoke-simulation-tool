# Configuration Files

This directory contains saved simulation configurations.

## Example Configurations

### example_single_sensor.json
- **Purpose**: Basic single-sensor setup
- **Sensors**: 1 pair at mid-room (30ft from fan)
- **Smokers**: 24 (moderate load)
- **Mode**: Automatic fan control
- **Use**: Quick testing and demonstrations

### example_three_sensors.json
- **Purpose**: Comprehensive room coverage
- **Sensors**: 3 pairs (near, middle, far)
- **Smokers**: 36 (heavy load)
- **Mode**: Automatic fan control
- **Use**: Production optimization

### example_maximum_capacity.json
- **Purpose**: Stress test with full capacity
- **Sensors**: 4 pairs (maximum coverage)
- **Smokers**: 48 (full capacity)
- **Mode**: Automatic fan control at 2x speed
- **Use**: Worst-case scenario analysis

## Creating Custom Configurations

1. Set up your desired configuration in the application
2. Click "Save Configuration" in the Simulation tab
3. Choose a descriptive filename
4. Configuration will be saved in this directory

## Configuration Format

Configurations are JSON files with the following structure:

```json
{
  "sensors": [
    {
      "pair_id": 0,
      "distance_from_fan": 30.0,
      "low_height": 3.0,
      "high_height": 12.0
    }
  ],
  "simulation": {
    "num_smokers": 24,
    "fan_mode": "auto",
    "simulation_speed": 1.0
  }
}
```

### Fields

- **sensors**: Array of sensor pair configurations
  - **pair_id**: Unique identifier (0-3)
  - **distance_from_fan**: Distance from fan in feet
  - **low_height**: Low sensor height from floor in feet
  - **high_height**: High sensor height from floor in feet

- **simulation**: Simulation parameters
  - **num_smokers**: Number of active smokers (0-48)
  - **fan_mode**: "manual" or "auto"
  - **simulation_speed**: Speed multiplier (0.1-10.0)
