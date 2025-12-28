# Fan Position and Sensor Wall Selection Update

## Summary

Successfully updated the smoke simulation tool with the following changes:

### 1. **Fan Position Updated** ✅

**Previous Position:** X=0.5, Y=18.0, Z=70.0 (near back wall)  
**New Position:** X=0.5, Y=17.5, Z=5.0 (near front wall)

The fan is now positioned:
- **Left Wall**: X=0.5 ft (6 inches from the left edge, X=0)
- **Height**: 17.5 ft (2.5 feet from the 20 ft ceiling)
- **Distance from Front**: 5 ft from the front wall (Z=0)

This is the **opposite** location from where sensors typically appear (back wall).

### 2. **Sensor Wall Selection Verified** ✅

The sensor wall selection dropdown was already implemented and is working correctly:

#### GUI Components:
- **Dropdown Location**: Sensor Pair Configuration panel
- **Options**: "Front Wall" or "Back Wall" (default: Back Wall)
- **Visibility**: Clearly labeled as "Sensor Wall:" with tooltip
- **Functionality**: Changes sensor Z-position based on selection

#### Sensor Positions:
- **Back Wall Sensors**: Z = 74.5 ft (6 inches from back wall at Z=75)
- **Front Wall Sensors**: Z = 0.5 ft (6 inches from front wall at Z=0)

#### Display Features:
- Sensor list shows wall: "Pair 0: Back Wall, 30.0ft from fan, Low:3.0ft, High:12.0ft"
- Sensor readings show wall: "Sensor Pair 0 (Back Wall): Low - PPM:45.2, Clarity:95.1%"

### 3. **Debug Output Added** ✅

Added console output to help verify positions:

#### When Simulation Starts:
```
============================================================
SIMULATION STARTED - CONFIGURATION
============================================================
Fan Position: X=0.5 ft, Y=17.5 ft, Z=5.0 ft
  (Left wall, 17.5 ft high, 5.0 ft from front wall)

Sensor Pairs: 2
  Pair 0 (Back Wall):
    Low:  X=0.0, Y=3.0, Z=74.5
    High: X=0.0, Y=12.0, Z=74.5
  Pair 1 (Front Wall):
    Low:  X=1.5, Y=4.0, Z=0.5
    High: X=1.5, Y=15.0, Z=0.5
============================================================
```

#### When Adding Sensors:
```
✓ Added Sensor Pair 0 on Back Wall:
  Low:  X=0.0, Y=3.0, Z=74.5
  High: X=0.0, Y=12.0, Z=74.5
```

## Room Layout Diagram

```
Top View (looking down at the floor):

                    FRONT WALL (Z=0)
        ┌─────────────────────────────────┐
        │                                 │
   L    │  🟦 Fan (X=0.5, Z=5)           │   R
   E    │                                 │   I
   F    │                                 │   G
   T    │                                 │   H
        │                                 │   T
   W    │                                 │
   A    │                                 │   W
   L    │                                 │   A
   L    │                                 │   L
        │                                 │   L
  (X=0) │  🔴 Sensors (Z=0.5 or Z=74.5)  │  (X=30)
        │                                 │
        └─────────────────────────────────┘
                    BACK WALL (Z=75)

Side View (looking from the right):

        ┌─────────────────────────────────┐ 20 ft (ceiling)
        │                                 │
        │  🟦 Fan (Y=17.5, Z=5)          │ 17.5 ft
        │                                 │
        │                                 │
        │                                 │
        │  🔴 High Sensor (Y=12)         │ 12 ft
        │                                 │
        │                                 │
        │  🔴 Low Sensor (Y=3)           │ 3 ft
        └─────────────────────────────────┘ 0 ft (floor)
        Z=0                              Z=75
```

## Files Modified

1. **utils/constants.py**
   - Updated `FAN_POSITION` from [0.5, 18.0, 70.0] to [0.5, 17.5, 5.0]

2. **gui/main_window.py**
   - Added debug output in `_start_simulation()` method
   - Added debug output in `_add_sensor_pair()` method
   - (Sensor wall dropdown was already implemented)

3. **Test Files Created**
   - `test_positions.py` - Basic position verification tests
   - `verify_complete_update.py` - Comprehensive verification script

## Verification Results

All verifications passed! ✅

- ✅ Fan position correct (X=0.5, Y=17.5, Z=5.0)
- ✅ Back wall sensors at Z=74.5 ft
- ✅ Front wall sensors at Z=0.5 ft
- ✅ Sensor wall dropdown visible and working
- ✅ GUI integration complete
- ✅ Debug output functional

## How to Use

### Running the Application:
```bash
cd /home/ubuntu/github_repos/smoke-simulation-tool
python main.py
```

### Adding Sensors:
1. In the "Sensor Pair Configuration" panel, select wall from dropdown
2. Set distance from fan, low height, and high height
3. Click "Add Sensor Pair"
4. The sensor list will show the wall selection
5. Debug output will confirm the position

### Viewing Sensor Positions:
- Check the terminal/console output when simulation starts
- Check the 3D visualization (sensors appear as colored markers)
- Check the sensor readings panel (shows wall for each pair)

## Git Commit

Changes have been committed and pushed to the `coord-mapping-fix` branch:

**Commit Message:**
> Fix fan position and verify sensor wall selection
>
> Changes:
> - Updated fan position to X=0.5, Y=17.5, Z=5.0 (left wall, 5ft from front)
> - Verified sensor wall selection dropdown is visible and working
> - Added debug output showing fan and sensor positions on simulation start
> - Added debug output when sensors are added
> - Created comprehensive test scripts

## Coordinate System Reference

- **X-axis (Width)**: 0 to 30 ft (Left to Right)
- **Y-axis (Height)**: 0 to 20 ft (Floor to Ceiling)
- **Z-axis (Length)**: 0 to 75 ft (Front to Back)

### Key Positions:
- **Fan**: Left wall (X=0.5), high up (Y=17.5), near front (Z=5)
- **Front Wall**: Z = 0 → Sensors at Z = 0.5
- **Back Wall**: Z = 75 → Sensors at Z = 74.5

---

**Status**: ✅ Complete and tested
**Branch**: coord-mapping-fix
**Date**: December 28, 2025
