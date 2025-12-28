# Fan Position & Sensor Wall Selection Update

**Date:** December 28, 2024  
**Status:** ✅ Completed and Tested

---

## Overview

This update implements two major improvements to the smoke simulation tool:
1. **Fan relocation** to the left wall with correct positioning
2. **Sensor wall selection** feature allowing sensors to be placed on either the front or back wall

---

## Changes Made

### 1. Fan Position Update

**File:** `utils/constants.py`

#### Previous Position:
- X = 5.0 ft (5 feet from left wall)
- Y = 15.0 ft (15 feet up from floor)
- Z = 75.0 ft (on back wall)

#### New Position:
- **X = 0.5 ft** (6 inches from left wall - ON LEFT WALL)
- **Y = 18.0 ft** (2 feet from top / 18 feet from floor)
- **Z = 70.0 ft** (5 feet from back wall)

```python
FAN_POSITION = np.array([0.5, 18.0, 70.0])  # On left wall (6 inches from edge), 2ft from top (18ft up), 5ft from back wall
```

**Visualization Impact:**
- Fan now appears on the left wall of the room
- Located high on the wall (near ceiling)
- 5 feet forward from the back wall

---

### 2. Sensor Wall Selection Feature

**Files Modified:**
- `simulation/sensor.py`
- `gui/main_window.py`
- `utils/config_manager.py`

#### A. Sensor Class Updates (`simulation/sensor.py`)

**Changes to `SensorPair` class:**

```python
def __init__(self, pair_id, distance_from_fan, low_height, high_height, fan_position, wall='back'):
    """
    Args:
        wall: Which wall to place sensors on ('front' or 'back')
    """
    self.wall = wall
    
    # Calculate Z position based on wall selection
    if wall.lower() == 'front':
        sensor_z = 0.5  # 6 inches from front wall
    else:  # back wall (default)
        sensor_z = 74.5  # 6 inches from back wall (ROOM_LENGTH=75, so 75-0.5=74.5)
```

**Sensor Positioning Logic:**
- **Front Wall:** Z = 0.5 ft (6 inches from front)
- **Back Wall:** Z = 74.5 ft (6 inches from back)
- X and Y coordinates remain based on existing logic (distance from fan, height)
- Both low and high sensors in a pair use the same wall

---

#### B. GUI Updates (`gui/main_window.py`)

**Added Wall Selection Dropdown:**

```python
config_layout.addWidget(QLabel("Sensor Wall:"), 0, 0)
self.combo_sensor_wall = QComboBox()
self.combo_sensor_wall.addItems(["Back Wall", "Front Wall"])
self.combo_sensor_wall.setToolTip("Select which wall to place sensors on (6 inches from wall)")
config_layout.addWidget(self.combo_sensor_wall, 0, 1)
```

**Updated Sensor Creation:**
```python
def _add_sensor_pair(self):
    # Get wall selection
    wall_text = self.combo_sensor_wall.currentText()
    wall = 'front' if wall_text == "Front Wall" else 'back'
    
    # Create sensor pair with wall selection
    sensor_pair = SensorPair(pair_id, distance, low_height, high_height, FAN_POSITION, wall)
```

**Enhanced Sensor List Display:**
- Now shows wall information: `"Pair 0: Back Wall, 30.0ft from fan, Low:3.0ft, High:12.0ft"`

**Updated Sensor Readings Display:**
```python
wall_name = "Front Wall" if pair.wall == 'front' else "Back Wall"
sensor_text += f"Sensor Pair {readings['pair_id']} ({wall_name}):\n"
```

**Configuration Loading:**
- Updated to support wall parameter
- Backward compatible with old configs (defaults to 'back' wall)

---

#### C. Configuration Manager Updates (`utils/config_manager.py`)

**Updated Config Save:**
```python
sensors_config.append({
    'pair_id': pair.pair_id,
    'distance_from_fan': pair.distance_from_fan,
    'low_height': pair.low_height,
    'high_height': pair.high_height,
    'wall': pair.wall  # NEW
})
```

---

### 3. Testing & Verification

**File:** `test_fan_sensor_update.py`

Created comprehensive test suite covering:
1. ✅ Fan position verification (X=0.5, Y=18, Z=70)
2. ✅ Back wall sensor positioning (Z=74.5)
3. ✅ Front wall sensor positioning (Z=0.5)
4. ✅ Room dimensions unchanged
5. ✅ Sensor heights correct
6. ✅ Wall parameter properly stored in SensorPair objects

**All tests passing successfully!**

---

## User Interface Changes

### Sensor Configuration Panel (Before)
```
┌─ Sensor Pair Configuration ──────────┐
│ Distance from Fan (ft): [30.0]       │
│ Low Sensor Height (ft): [3.0]        │
│ High Sensor Height (ft): [12.0]      │
└──────────────────────────────────────┘
```

### Sensor Configuration Panel (After)
```
┌─ Sensor Pair Configuration ──────────┐
│ Sensor Wall:           [Back Wall ▼] │  ← NEW!
│ Distance from Fan (ft): [30.0]       │
│ Low Sensor Height (ft): [3.0]        │
│ High Sensor Height (ft): [12.0]      │
└──────────────────────────────────────┘
```

### Sensor List Display
**Before:** `Pair 0: 30.0ft from fan, Low:3.0ft, High:12.0ft`  
**After:** `Pair 0: Back Wall, 30.0ft from fan, Low:3.0ft, High:12.0ft`

### Sensor Readings Display
**Before:**
```
Sensor Pair 0:
  Low  - PPM: 45.2, Clarity: 95.1%
  High - PPM: 32.8, Clarity: 97.3%
```

**After:**
```
Sensor Pair 0 (Back Wall):
  Low  - PPM: 45.2, Clarity: 95.1%
  High - PPM: 32.8, Clarity: 97.3%
```

---

## Coordinate System Reference

For clarity, here's the room coordinate system:

```
┌─────────────────────────────────────┐
│ Room Dimensions:                    │
│   Width (X):  0 - 30 ft            │
│   Height (Y): 0 - 20 ft            │
│   Length (Z): 0 - 75 ft            │
└─────────────────────────────────────┘

Walls:
  • Left Wall:  X = 0 ft
  • Right Wall: X = 30 ft
  • Floor:      Y = 0 ft
  • Ceiling:    Y = 20 ft
  • Front Wall: Z = 0 ft
  • Back Wall:  Z = 75 ft

Fan Position (NEW):
  • X = 0.5 ft  → On LEFT WALL (6 inches from edge)
  • Y = 18 ft   → Near ceiling (2 ft from top)
  • Z = 70 ft   → 5 feet from back wall

Sensor Positions:
  • Front Wall: Z = 0.5 ft (6 inches from front)
  • Back Wall:  Z = 74.5 ft (6 inches from back)
  • X: Based on fan X + offset (spread to avoid overlap)
  • Y: User-specified height (low/high)
```

---

## Backward Compatibility

✅ **Fully backward compatible!**

- Old configuration files without `wall` parameter will default to `'back'` wall
- Existing saved configurations will load correctly
- No breaking changes to API or data structures

---

## Files Modified Summary

| File | Changes |
|------|---------|
| `utils/constants.py` | Updated FAN_POSITION to [0.5, 18.0, 70.0] |
| `simulation/sensor.py` | Added wall parameter to SensorPair, updated positioning logic |
| `gui/main_window.py` | Added wall dropdown, updated sensor creation/display/loading |
| `utils/config_manager.py` | Added wall to config save dictionary |
| `test_fan_sensor_update.py` | **NEW** - Comprehensive test suite |

---

## Usage Instructions

### Adding Sensors with Wall Selection

1. Open the application
2. Go to the **Sensors** tab
3. Configure your sensor pair:
   - **Select Wall**: Choose "Front Wall" or "Back Wall" from dropdown
   - **Distance from Fan**: Horizontal offset (affects X position)
   - **Low Sensor Height**: Height of lower sensor (3-19 ft)
   - **High Sensor Height**: Height of upper sensor (3-19 ft)
4. Click **"Add Sensor Pair"**

### Visualizing Sensors

- Sensors on the **back wall** (Z=74.5) will appear near the far edge in 3D view
- Sensors on the **front wall** (Z=0.5) will appear near the close edge in 3D view
- Fan now appears on the **left wall** (X=0.5) near the top (Y=18)

### Configuration Files

Sensor configurations are now saved with wall information:
```json
{
  "sensors": [
    {
      "pair_id": 0,
      "distance_from_fan": 30.0,
      "low_height": 3.0,
      "high_height": 12.0,
      "wall": "back"
    }
  ]
}
```

---

## Testing Results

```
██████████████████████████████████████████████████████████████████████
✓ ALL TESTS PASSED!
██████████████████████████████████████████████████████████████████████

Summary:
  • Fan moved to left wall (X=0.5, Y=18, Z=70)
  • Sensors can be placed on front wall (Z=0.5) or back wall (Z=74.5)
  • Wall selection properly affects sensor Z-coordinate
  • Heights and X-offsets work correctly
```

---

## Git Commit

```
commit 88028d4
Author: [Author]
Date: [Date]

Update fan position and add sensor wall selection

- Moved fan to left wall: X=0.5, Y=18, Z=70 (6in from left, 2ft from top, 5ft from back)
- Added sensor wall selection dropdown in GUI (Front Wall or Back Wall)
- Sensors now placed 6 inches from selected wall:
  * Front Wall: Z=0.5 ft
  * Back Wall: Z=74.5 ft
- Updated sensor display to show which wall sensors are on
- Updated config save/load to include wall parameter
- Added comprehensive test suite to verify changes
- All tests passing
```

---

## Next Steps / Future Enhancements

Potential improvements for future updates:
- [ ] Add tooltips showing sensor coordinates when hovering in 3D view
- [ ] Allow custom Z-positioning (not just fixed walls)
- [ ] Add visual indicators showing which wall is selected
- [ ] Allow editing existing sensor pairs to change wall
- [ ] Add sensor placement validation (warn if too close to fan)

---

## Conclusion

✅ **All tasks completed successfully!**

The fan has been relocated to the left wall at the correct position, and sensors can now be flexibly placed on either the front or back wall. The implementation is clean, well-tested, and backward compatible with existing configurations.

The user interface is intuitive with clear labels, and the sensor readings display now shows which wall each sensor pair is mounted on. All changes have been committed to git with comprehensive testing.
