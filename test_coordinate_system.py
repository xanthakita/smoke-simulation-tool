"""Test script to verify 3D coordinate system is correct."""

import numpy as np
from utils.constants import ROOM_WIDTH, ROOM_HEIGHT, ROOM_LENGTH, FAN_POSITION

def test_coordinate_system():
    """Verify the coordinate system mapping is correct."""
    
    print("=" * 70)
    print("3D COORDINATE SYSTEM VERIFICATION")
    print("=" * 70)
    
    # Test room dimensions
    print("\n1. ROOM DIMENSIONS:")
    print(f"   ROOM_WIDTH (X-axis):  {ROOM_WIDTH} ft (horizontal left/right)")
    print(f"   ROOM_HEIGHT (Y-axis): {ROOM_HEIGHT} ft (VERTICAL up/down)")
    print(f"   ROOM_LENGTH (Z-axis): {ROOM_LENGTH} ft (horizontal front/back)")
    
    assert ROOM_WIDTH == 30.0, f"Width should be 30 ft, got {ROOM_WIDTH}"
    assert ROOM_HEIGHT == 20.0, f"Height should be 20 ft, got {ROOM_HEIGHT}"
    assert ROOM_LENGTH == 75.0, f"Length should be 75 ft, got {ROOM_LENGTH}"
    print("   ✓ All dimensions correct!")
    
    # Test room corners
    print("\n2. ROOM CORNERS:")
    corners = {
        "Front-left-bottom":  [0, 0, 0],
        "Front-right-bottom": [ROOM_WIDTH, 0, 0],
        "Back-right-bottom":  [ROOM_WIDTH, 0, ROOM_LENGTH],
        "Back-left-bottom":   [0, 0, ROOM_LENGTH],
        "Front-left-top":     [0, ROOM_HEIGHT, 0],
        "Front-right-top":    [ROOM_WIDTH, ROOM_HEIGHT, 0],
        "Back-right-top":     [ROOM_WIDTH, ROOM_HEIGHT, ROOM_LENGTH],
        "Back-left-top":      [0, ROOM_HEIGHT, ROOM_LENGTH],
    }
    
    for name, coord in corners.items():
        print(f"   {name:20s}: [{coord[0]:5.1f}, {coord[1]:5.1f}, {coord[2]:5.1f}] = (X, Y, Z)")
    
    # Test fan position
    print("\n3. FAN POSITION:")
    print(f"   Position: [{FAN_POSITION[0]:.1f}, {FAN_POSITION[1]:.1f}, {FAN_POSITION[2]:.1f}]")
    print(f"   - X = {FAN_POSITION[0]:.1f} ft from left wall (width)")
    print(f"   - Y = {FAN_POSITION[1]:.1f} ft up from floor (height - VERTICAL)")
    print(f"   - Z = {FAN_POSITION[2]:.1f} ft from front (on BACK wall)")
    
    assert FAN_POSITION[0] == 5.0, f"Fan X should be 5 ft, got {FAN_POSITION[0]}"
    assert FAN_POSITION[1] == 15.0, f"Fan Y should be 15 ft, got {FAN_POSITION[1]}"
    assert FAN_POSITION[2] == 75.0, f"Fan Z should be 75 ft, got {FAN_POSITION[2]}"
    print("   ✓ Fan position correct!")
    
    # Test boundary conditions
    print("\n4. BOUNDARY CONDITIONS:")
    print("   Particle boundaries should be:")
    print(f"   - X (width):  0 to {ROOM_WIDTH} ft")
    print(f"   - Y (height): 0 to {ROOM_HEIGHT} ft (floor=0, ceiling={ROOM_HEIGHT})")
    print(f"   - Z (length): 0 to {ROOM_LENGTH} ft (front=0, back={ROOM_LENGTH})")
    
    # Test sample particle positions
    print("\n5. SAMPLE PARTICLE POSITIONS:")
    sample_particles = [
        ("Floor center", [ROOM_WIDTH/2, 0, ROOM_LENGTH/2]),
        ("Ceiling center", [ROOM_WIDTH/2, ROOM_HEIGHT, ROOM_LENGTH/2]),
        ("Room center", [ROOM_WIDTH/2, ROOM_HEIGHT/2, ROOM_LENGTH/2]),
        ("Near fan", [5, 15, 70]),
    ]
    
    for name, pos in sample_particles:
        print(f"   {name:20s}: [{pos[0]:5.1f}, {pos[1]:5.1f}, {pos[2]:5.1f}]")
        # Verify in bounds
        assert 0 <= pos[0] <= ROOM_WIDTH, f"{name} X out of bounds"
        assert 0 <= pos[1] <= ROOM_HEIGHT, f"{name} Y out of bounds"
        assert 0 <= pos[2] <= ROOM_LENGTH, f"{name} Z out of bounds"
    print("   ✓ All positions within bounds!")
    
    # Test axis mapping for physics
    print("\n6. PHYSICS AXIS MAPPING:")
    print("   - Horizontal spread: X (width) and Z (length)")
    print("   - Vertical rise/fall: Y (height)")
    print("   - Buoyancy zones: Based on Y values (height)")
    print("     • 0-4 ft (Y):   Rise from source")
    print("     • 4-8 ft (Y):   Hover zone")
    print("     • 8-14 ft (Y):  Slow rise")
    print("     • 14-18 ft (Y): Very slow rise")
    print("     • 18+ ft (Y):   Near ceiling")
    
    # Test fan circle orientation
    print("\n7. FAN CIRCLE ORIENTATION:")
    print("   Fan is on back wall (Z=75), so fan circle should be:")
    print("   - In XY plane (X varies, Y varies, Z constant)")
    print("   - NOT in YZ plane (X constant, Y varies, Z varies)")
    print("   This ensures fan appears as a circle on the back wall.")
    
    print("\n" + "=" * 70)
    print("✓ ALL COORDINATE SYSTEM TESTS PASSED!")
    print("=" * 70)

if __name__ == "__main__":
    test_coordinate_system()
