# Cigar Lounge Smoke Simulation Tool

## Overview
A comprehensive Python-based smoke simulation tool designed for optimizing exhaust fan and sensor placement in a cigar lounge environment. The application provides real-time 3D visualization, physics-based smoke dispersion, and intelligent fan control.

## Features
- **3D Room Visualization**: Real-time particle-based smoke rendering
- **Sensor Placement**: Configure 1-4 pairs of sensors with customizable positions
- **Physics Simulation**: Accurate smoke dispersion with diffusion, convection, and buoyancy
- **Fan Control**: Manual and automatic modes with intelligent sensor-based control
- **Data Analysis**: Real-time graphs, statistics, and CSV export
- **Configuration Management**: Save and load sensor configurations

## Room Specifications
- **Dimensions**: 30ft (W) × 75ft (L) × 20ft (H)
- **Exhaust Fan**: 28.8" diameter, located 15ft up on back wall, 5ft from right wall
- **Capacity**: Up to 48 simultaneous smoking sources
- **Fan Range**: 0-100% variable speed (three-phase)

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup
```bash
# Clone or download the project
cd smoke_simulation_tool

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Running the Application
```bash
python main.py
```

### Basic Workflow
1. **Configure Sensors**: Click "Add Sensor Pair" to place sensors. Set their distance from fan and heights.
2. **Set Smoke Sources**: Adjust the number of active smokers (1-48)
3. **Start Simulation**: Click "Start Simulation" to begin
4. **Fan Control**: Choose between manual or automatic fan control
5. **Monitor Data**: Watch real-time graphs and 3D visualization
6. **Export Results**: Save data to CSV for further analysis

## Control Logic

### Sensor System
- **Low Sensor**: Determines timing/duration before rechecking air quality
- **High Sensor**: Determines required fan speed based on particle concentration
- **Measurements**: 
  - Particle PPM (parts per million)
  - Air clarity percentage (visual transmission)

### Fan Controller
The automatic fan controller uses a multi-sensor approach:
1. Reads all sensor pairs continuously
2. Low sensors determine if air quality is acceptable
3. High sensors detect heavy smoke concentration
4. Controller adjusts fan speed based on worst readings
5. Fan ramps down gradually when air quality improves

## Interface Guide

### Main Window Components
- **3D View**: Shows room, sensors, fan, and smoke particles
- **Control Panel**: Start/stop, reset, simulation speed
- **Sensor Configuration**: Add/remove sensors, set positions
- **Fan Control**: Manual/auto mode, speed slider
- **Data Display**: Real-time sensor readings
- **Graphs**: PPM, clarity, and fan speed over time

### Keyboard Shortcuts
- **Space**: Start/Pause simulation
- **R**: Reset simulation
- **F**: Toggle fan mode (manual/auto)
- **+/-**: Adjust simulation speed
- **Arrow Keys**: Rotate 3D view

## Physics Model

The simulation uses a particle-based approach with the following physics:

### Smoke Dispersion
- **Diffusion**: Random walk based on temperature and air viscosity
- **Convection**: Air currents created by temperature gradients
- **Buoyancy**: Upward force on hot smoke particles
- **Advection**: Air flow toward exhaust fan

### Fan Modeling
- **Airflow**: Calculated using fan diameter and speed
- **Velocity Field**: Inverse square law from fan location
- **Boundary Conditions**: Replacement air enters from bottom

### Sensor Readings
- **PPM Calculation**: Count particles within sensor volume
- **Air Clarity**: Beer-Lambert law for light transmission
- **Response Time**: Realistic sensor lag (~1-2 seconds)

## Configuration Files

Configurations are saved in JSON format in the `configs/` directory:
```json
{
  "sensors": [
    {
      "id": 0,
      "distance_from_fan": 10.0,
      "low_height": 3.0,
      "high_height": 12.0
    }
  ],
  "simulation": {
    "num_smokers": 24,
    "particle_gen_rate": 1000,
    "fan_mode": "auto"
  }
}
```

## Data Export

Exported CSV files contain:
- Timestamp
- Each sensor's PPM reading
- Each sensor's clarity reading
- Fan speed percentage
- Room average PPM
- Room average clarity

## Performance Notes

- **Particle Count**: Simulation manages 10,000-50,000 particles
- **Update Rate**: 30-60 FPS depending on hardware
- **Accuracy**: Time step of 0.1 seconds for physics
- **Optimization**: Numba JIT compilation for critical loops

## Troubleshooting

### Common Issues

**3D view not rendering:**
- Ensure PyOpenGL is properly installed
- Update graphics drivers
- Try running with `python main.py --no-accel`

**Slow performance:**
- Reduce number of smokers
- Lower particle generation rate in settings
- Disable real-time rendering updates

**Sensor readings seem incorrect:**
- Check sensor positions are inside room bounds
- Verify fan is enabled and running
- Reset simulation and try again

## Future Enhancements

- Replacement air duct modeling
- Multiple fan support
- Web-based interface
- Real hardware integration
- CFD validation comparisons

## Technical Details

### Coordinate System
- Origin (0,0,0) at front-left-floor corner
- X-axis: Width (0-30 ft)
- Y-axis: Height (0-20 ft)
- Z-axis: Length (0-75 ft)
- Fan position: (25ft, 15ft, 75ft)

### Units
- Distance: Feet (ft)
- Time: Seconds (s)
- Speed: Feet per second (ft/s)
- Concentration: Parts per million (PPM)
- Clarity: Percentage (0-100%)

## License
This project is provided as-is for educational and optimization purposes.

## Support
For questions or issues, please refer to the documentation or contact the development team.
