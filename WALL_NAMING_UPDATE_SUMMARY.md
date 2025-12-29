# Wall Naming Convention and Fan/Sensor Repositioning Update

## Summary
This update changes the wall naming convention from relative terms (Front/Back/Left/Right) to compass directions (North/South/East/West), and repositions the fan and sensors according to the new coordinate system.

## Coordinate System
- **x-axis (Width, 0-30 ft)**:
  - North Wall: x ≈ 0
  - South Wall: x ≈ 30

- **y-axis (Height, 0-20 ft)**:
  - Floor: y = 0
  - Ceiling: y = 20

- **z-axis (Length, 0-75 ft)**:
  - East Wall: z ≈ 0
  - West Wall: z ≈ 75

## Changes Made

### 1. Fan Position Update (`utils/constants.py`)
**Previous Position:** `[0.5, 17.5, 5.0]`
- On Left wall (x≈0), 17.5ft high, 5ft from Front wall

**New Position:** `[5.0, 14.0, 0.5]`
- On East wall (z≈0), 14ft high, 5ft from North wall (x≈0)

```python
FAN_POSITION = np.array([5.0, 14.0, 0.5])  # On East wall (z≈0), 14ft high, 5ft from North wall (x≈0)
```

### 2. Sensor Placement Logic Update (`simulation/sensor.py`)
**Previous:** Sensors placed on Front/Back walls (z-axis placement)
- Front Wall: z = 0.5
- Back Wall: z = 74.5

**New:** Sensors placed on North/South walls (x-axis placement)
- North Wall: x = 0.5 (6 inches from North wall)
- South Wall: x = 29.5 (6 inches from South wall)

Key changes:
- Changed default wall from `'back'` to `'south'`
- Sensor position calculation now uses x-axis for wall placement
- Z-position now spreads sensors along the length of the wall

```python
# Calculate X position based on wall selection
if wall.lower() == 'north':
    sensor_x = 0.5  # 6 inches from North wall (x≈0)
else:  # south wall (default)
    sensor_x = 29.5  # 6 inches from South wall (ROOM_WIDTH=30, so 30-0.5=29.5)
```

### 3. GUI Updates (`gui/main_window.py`)
**Dropdown Options Changed:**
- Old: "Front Wall", "Back Wall"
- New: "North Wall", "South Wall"

**Wall Selection Logic:**
```python
wall = 'north' if wall_text == "North Wall" else 'south'
```

**Display Updates:**
- Sensor list display now shows "North Wall" or "South Wall"
- Sensor readings display updated to show compass directions
- Debug output updated to reflect new wall naming

### 4. Code Comments and Documentation Updates
Updated comments in the following files to use compass directions:
- `simulation/room.py`: Updated margin comments
- `simulation/smoke_physics.py`: Updated boundary condition comments
- `visualization/renderer_3d.py`: Updated fan orientation comments

### 5. Wall Naming Convention
**Old Convention:**
- Left Wall (x≈0)
- Right Wall (x≈30)
- Front Wall (z≈0)
- Back Wall (z≈75)

**New Convention:**
- North Wall (x≈0)
- South Wall (x≈30)
- East Wall (z≈0)
- West Wall (z≈75)

## Coordinate System Consistency
The coordinate system remains consistent with:
- Sensors now placed perpendicular to the original orientation
- Fan repositioned to East wall instead of Left wall
- All wall references use compass directions for clarity
- Compass directions are absolute and independent of camera rotation

## Backward Compatibility
- Configuration files with old wall names ('front', 'back') will default to 'south' for safety
- No breaking changes to the simulation physics or core functionality

## Files Modified
1. `utils/constants.py` - Fan position constant
2. `simulation/sensor.py` - Sensor placement logic
3. `gui/main_window.py` - GUI dropdowns and display text
4. `simulation/room.py` - Margin comments
5. `simulation/smoke_physics.py` - Boundary condition comments
6. `visualization/renderer_3d.py` - Fan orientation comments

## Testing Recommendations
1. Verify fan appears on East wall at correct position
2. Verify sensors can be placed on North and South walls
3. Test that sensor readings work correctly with new positions
4. Check 3D visualization shows correct positioning
5. Verify configuration save/load works with new wall names
