# 3D Visualization Coordinate System Fix

## Issue
The 3D visualization was displaying the room with incorrect orientation, making it appear "on its side" with axes mislabeled or confusingly positioned.

## Coordinate System Definition

### Standard Coordinate Mapping
The simulation uses the following coordinate system consistently throughout:

```
- X-axis: Width (0-30 ft) - horizontal left/right
- Y-axis: Height (0-20 ft) - VERTICAL up/down  
- Z-axis: Length (0-75 ft) - horizontal front/back (depth)
```

### Room Corners (for reference)
```
Front face (Z=0):
  - Front-left-bottom:  (0, 0, 0)
  - Front-right-bottom: (30, 0, 0)
  - Front-left-top:     (0, 20, 0)
  - Front-right-top:    (30, 20, 0)

Back face (Z=75):
  - Back-left-bottom:   (0, 0, 75)
  - Back-right-bottom:  (30, 0, 75)
  - Back-left-top:      (0, 20, 75)
  - Back-right-top:     (30, 20, 75)
```

## Changes Made to `visualization/renderer_3d.py`

### 1. Camera View Angle Adjustment
**Before:**
```python
self.camera_elevation = 30.0
self.camera_azimuth = -45.0
```

**After:**
```python
self.camera_elevation = 20.0   # Look slightly down from above
self.camera_azimuth = -60.0    # View from front-left corner
```

**Reason:** The new angles provide a better perspective showing the room upright with Y-axis clearly vertical.

### 2. Enhanced Axis Setup
Added comprehensive documentation and improved axis labels:
- Clear dimension indicators in labels
- Room dimensions shown in title (30×20×75 ft)
- Added aspect ratio correction using `set_box_aspect()`
- Detailed comments explaining coordinate system

### 3. Room Drawing Corrections
**Floor and Ceiling:**
- Floor rectangle at Y=0 (bottom)
- Ceiling rectangle at Y=20 (top)
- Both drawn in XZ plane (horizontal planes)

**Floor Grid:**
- Grid lines properly drawn on Y=0 plane
- Lines parallel to Z-axis at X intervals
- Lines parallel to X-axis at Z intervals

### 4. Fan Positioning Fix
**Critical Fix:** Fan circle orientation was incorrect.

**Before:** Fan drawn in YZ plane (vertical circle)
```python
circle_x = np.full(segments + 1, pos[0])  # Constant X
circle_y = pos[1] + radius * np.cos(angles)  # Y varies
circle_z = pos[2] + radius * np.sin(angles)  # Z varies
```

**After:** Fan drawn in XY plane at back wall (Z=75)
```python
circle_x = pos[0] + radius * np.cos(angles)  # X varies
circle_y = pos[1] + radius * np.sin(angles)  # Y varies  
circle_z = np.full(segments + 1, pos[2])     # Constant Z=75
```

**Reason:** Fan is on back wall (Z=75), so circle should be perpendicular to Z-axis, lying in the XY plane.

### 5. Sensor Visualization Enhancement
- Increased marker size (100 → 120)
- Increased edge thickness (1.0 → 1.5)
- Enhanced connecting line visibility
- Added documentation explaining sensor positions

### 6. Particle Rendering
- Added `depthshade=True` for better 3D perception
- Comprehensive documentation of particle coordinate mapping
- Verified correct axis usage (X=width, Y=height, Z=depth)

## Element Positions Verification

### Fan
```
Position: [5.0, 15.0, 75.0]
- 5 ft from left wall (X)
- 15 ft up from floor (Y)
- On back wall (Z=75)
```

### Sensors
```
Each pair has:
- X: Spread across width based on pair ID
- Y: low_height (e.g., 5 ft) and high_height (e.g., 15 ft)
- Z: Distance from back wall toward front
```

### Smoke Particles
```
Positions: (N, 3) numpy array
- Column 0: X (width, 0-30 ft)
- Column 1: Y (height, 0-20 ft) - vertical movement
- Column 2: Z (depth, 0-75 ft)
```

## Physics Integration

The coordinate system matches the physics simulation:

### Boundary Conditions (`smoke_physics.py`)
```python
# X boundaries (width)
mask = self.particles_positions[:, 0] < 0 or > ROOM_WIDTH

# Y boundaries (height - vertical)  
mask = self.particles_positions[:, 1] < 0 or > ROOM_HEIGHT

# Z boundaries (length - depth)
mask = self.particles_positions[:, 2] < 0 or > ROOM_LENGTH
```

### Smoke Behavior
- **Horizontal spread:** X and Z components (with diffusion multipliers)
- **Vertical rise:** Y component (with height-dependent buoyancy)
- **Stratification:** Height zones defined by Y values (4-8 ft hover zone, etc.)

## Expected Visual Result

After these fixes, the 3D view should display:

1. **Upright Room:** Y-axis clearly vertical (floor at bottom, ceiling at top)
2. **Correct Dimensions:** 30×20×75 ft visible in title and axis ranges
3. **Fan on Back Wall:** Circular fan at correct position (X=5, Y=15, Z=75)
4. **Sensors Positioned Correctly:** Vertical pairs spread across room
5. **Smoke Particles:** Rising vertically and spreading horizontally
6. **Natural View Angle:** Looking down from front-left corner

## Testing

To verify the fixes:
1. Launch the application: `python main.py`
2. Start simulation with 4 cigars
3. Verify:
   - Room appears upright with Y-axis vertical
   - Fan circle is visible on back wall (not floating in space)
   - Smoke particles rise vertically and spread horizontally
   - Sensor pairs show vertical alignment
   - All dimensions match 30×20×75 ft

## Files Modified
- `visualization/renderer_3d.py` - Complete coordinate system documentation and fixes

## Files Verified (Already Correct)
- `utils/constants.py` - Room dimensions correct (30×20×75)
- `simulation/smoke_physics.py` - Boundary conditions use correct axes
- `simulation/sensor.py` - Sensor positioning uses correct coordinates
- `simulation/fan.py` - Fan position correct [5, 15, 75]
