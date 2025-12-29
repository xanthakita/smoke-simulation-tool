# Trip Control Feature

## Overview

The Trip Control feature provides automated fan control based on sensor readings, activating the exhaust fan when air quality thresholds are exceeded and maintaining operation for a configurable duration.

## How It Works

### Basic Concept

1. **Sensors Monitor Air Quality**: Each sensor pair continuously monitors smoke concentration (PPM) and Air Quality Index (AQI)
2. **Threshold Detection**: When readings exceed configured thresholds, the sensor "trips"
3. **Fan Activation**: The exhaust fan activates automatically when any sensor trips
4. **Duration Timer**: Once tripped, the fan runs for a configured duration
5. **Automatic Shutoff**: The fan turns off automatically when all trip timers expire

### Trip Condition

A sensor pair trips when **either** of these conditions is met:
- **PPM exceeds threshold** (Parts Per Million of smoke particles)
- **AQI exceeds threshold** (Air Quality Index calculated from PM2.5 concentration)

### Fan Speed Calculation

When trip mode is active, fan speed is determined by the **highest AQI** among all tripped sensors:

| AQI Range | Air Quality Category | Fan Speed |
|-----------|---------------------|-----------|
| 0-50 | Good | 20% |
| 51-100 | Moderate | 40% |
| 101-150 | Unhealthy for Sensitive | 60% |
| 151-200 | Unhealthy | 80% |
| 201-500+ | Very Unhealthy/Hazardous | 100% |

### Multi-Sensor Coordination

When multiple sensors are tripped:
- **Fan speed** is based on the **highest AQI** among all tripped sensors
- **Run duration** uses the **longest remaining duration** from any tripped sensor
- This ensures adequate ventilation for the worst affected area

### Trip Duration Behavior

**Important**: The trip duration timer only starts counting down **after** readings drop below the threshold.

#### Timeline Example:
1. **t=0s**: Normal operation, readings below threshold
2. **t=10s**: Smoke detected, PPM/AQI exceeds threshold
3. **t=10s**: Sensor trips, fan activates, duration timer = 300s
4. **t=10-40s**: Readings remain above threshold → duration stays at 300s
5. **t=40s**: Readings drop below threshold → duration starts counting down
6. **t=340s**: Duration expires (300s after readings dropped), fan turns off

This design ensures the fan continues running until:
1. Air quality improves (readings drop below threshold)
2. AND the configured duration elapses

## Configuration

### Sensor Pair Settings

Each sensor pair has three trip control parameters:

```json
{
  "trip_ppm": 75,           // PPM threshold (0-1000)
  "trip_aqi": 125,          // AQI threshold (0-500)
  "trip_duration": 300      // Duration in seconds (0-3600)
}
```

### Example Configuration

**Conservative Settings** (triggers easily, longer duration):
```json
{
  "trip_ppm": 50,
  "trip_aqi": 100,
  "trip_duration": 360
}
```

**Moderate Settings** (balanced):
```json
{
  "trip_ppm": 75,
  "trip_aqi": 125,
  "trip_duration": 300
}
```

**Aggressive Settings** (triggers less often, shorter duration):
```json
{
  "trip_ppm": 100,
  "trip_aqi": 150,
  "trip_duration": 180
}
```

### Recommended Settings by Location

**Near Fan (0-20ft)**:
- Higher thresholds (smoke clears quickly)
- Shorter duration
- Example: PPM=150, AQI=175, Duration=180s

**Mid-Room (20-45ft)**:
- Moderate thresholds
- Standard duration
- Example: PPM=100, AQI=150, Duration=300s

**Far From Fan (45-75ft)**:
- Lower thresholds (smoke lingers longer)
- Longer duration
- Example: PPM=50, AQI=100, Duration=360s

## Usage

### Via GUI

1. **Add Sensor Pairs**:
   - Navigate to "Sensors" tab
   - Click "Add Sensor Pair"
   - Configure position and trip settings

2. **Enable Trip Mode**:
   - Navigate to "Fan Control" tab
   - Select "Trip (Sensor-Based)" mode
   - Sensors now control fan automatically

3. **Monitor Status**:
   - "Sensors" tab shows individual sensor trip status
   - "Fan Control" tab shows overall trip controller status
   - Red indicators show tripped sensors with countdown timers

### Via Configuration File

Create or load a config file with trip settings:

```json
{
  "sensors": [
    {
      "pair_id": 0,
      "distance_from_fan": 30.0,
      "low_height": 3.0,
      "high_height": 12.0,
      "wall": "south",
      "trip_ppm": 75,
      "trip_aqi": 125,
      "trip_duration": 300
    }
  ],
  "simulation": {
    "num_smokers": 24,
    "fan_mode": "trip",
    "simulation_speed": 1.0
  }
}
```

## Technical Details

### AQI Calculation

The system converts PPM readings to AQI using EPA PM2.5 breakpoints:

1. **PPM to µg/m³**: `concentration = ppm × 2.5`
2. **µg/m³ to AQI**: Linear interpolation using EPA breakpoints

### Sensor Response Time

Sensors have realistic response characteristics:
- **Update Rate**: 10 Hz (0.1 second intervals)
- **History Buffer**: 10 samples
- **Smoothing**: Moving average over history
- **Response Time**: ~1 second to stabilize

This means readings don't instantly drop to zero when particles clear - they gradually decrease as the history buffer updates.

### Fan Ramping

The fan speed ramps gradually rather than changing instantly:
- **Default Ramp Rate**: 10% per second
- **Smooth Operation**: Prevents sudden changes
- **Realistic Behavior**: Mimics actual exhaust fan behavior

## Integration with Simulation

### Main Loop Integration

The trip controller integrates with the simulation loop:

```python
# In main simulation loop
def update_simulation(dt):
    # Update sensors
    for sensor_pair in sensor_pairs:
        sensor_pair.update(particles, dt)
    
    # Update trip controller (if in trip mode)
    if fan_mode == 'trip':
        trip_controller.update(dt)
    
    # Update fan (handles ramping)
    fan.update(dt)
```

### Mode Switching

Three fan control modes are available:
1. **Manual**: User controls fan speed directly via slider
2. **Auto (PID)**: PID controller maintains target PPM
3. **Trip**: Sensor-based activation (this feature)

Switching modes resets controller state:
- Trip timers reset
- Fan ramps to new target speed
- Controllers disable conflicting modes

## Testing

Comprehensive test suite validates trip control functionality:

1. **Single Sensor Trip**: Verifies basic trip activation
2. **Multiple Sensors**: Tests longest duration coordination
3. **AQI-Based Speed**: Confirms fan speed increases with AQI
4. **Trip Expiration**: Validates automatic shutoff
5. **Mode Switching**: Tests clean transitions

Run tests:
```bash
python tests/test_trip_control.py
```

## Troubleshooting

### Issue: Fan doesn't turn on when sensor shows high readings
**Solution**: 
- Check trip mode is enabled ("Trip (Sensor-Based)")
- Verify trip thresholds aren't too high
- Ensure sensor is actually detecting particles (check readings)

### Issue: Fan stays on too long after smoke clears
**Possible Causes**:
- **Expected Behavior**: Duration timer only starts after readings drop below threshold
- **Sensor History**: Takes ~1 second for readings to stabilize after particles clear
- **Trip Duration**: Check configured duration isn't too long

### Issue: Fan doesn't turn off
**Solution**:
- Readings likely still above threshold (check PPM/AQI)
- Wait for sensor history to clear (10 samples × 0.1s = 1s minimum)
- Then wait for trip duration to expire

### Issue: Multiple sensors give inconsistent behavior
**Solution**:
- System uses **longest duration** from all tripped sensors
- System uses **highest AQI** for fan speed
- This is correct behavior for worst-case ventilation

## Future Enhancements

Potential improvements for future versions:
- Configurable fan speed curves
- Time-of-day scheduling
- Historical trip logging and analytics
- Email/SMS notifications on trip events
- Integration with building management systems
- Predictive trip based on smoke trends

## References

- **EPA AQI Breakpoints**: [EPA Air Quality Index Guide](https://www.airnow.gov/aqi/)
- **PM2.5 Standards**: EPA National Ambient Air Quality Standards
- **Sensor Technology**: Based on commercial smoke/particulate sensors
