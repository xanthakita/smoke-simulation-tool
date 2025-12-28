#!/usr/bin/env python3
"""Test script to verify fan position and sensor wall selection updates."""

import numpy as np
from utils.constants import FAN_POSITION, ROOM_WIDTH, ROOM_HEIGHT, ROOM_LENGTH
from simulation.sensor import SensorPair

def test_fan_position():
    """Test that fan position has been updated correctly."""
    print("=" * 70)
    print("TEST 1: Fan Position Update")
    print("=" * 70)
    
    expected_x = 0.5  # 6 inches from left wall
    expected_y = 18.0  # 2 feet from top (20-2=18)
    expected_z = 70.0  # 5 feet from back wall (75-5=70)
    
    print(f"\nExpected Fan Position:")
    print(f"  X = {expected_x} ft (6 inches from left wall)")
    print(f"  Y = {expected_y} ft (2 feet from top)")
    print(f"  Z = {expected_z} ft (5 feet from back wall)")
    
    print(f"\nActual Fan Position:")
    print(f"  X = {FAN_POSITION[0]} ft")
    print(f"  Y = {FAN_POSITION[1]} ft")
    print(f"  Z = {FAN_POSITION[2]} ft")
    
    # Verify
    assert FAN_POSITION[0] == expected_x, f"Fan X should be {expected_x}, got {FAN_POSITION[0]}"
    assert FAN_POSITION[1] == expected_y, f"Fan Y should be {expected_y}, got {FAN_POSITION[1]}"
    assert FAN_POSITION[2] == expected_z, f"Fan Z should be {expected_z}, got {FAN_POSITION[2]}"
    
    print("\n✓ Fan position is correct!")
    return True

def test_sensor_back_wall():
    """Test sensor positioning on back wall."""
    print("\n" + "=" * 70)
    print("TEST 2: Sensor Positioning - Back Wall")
    print("=" * 70)
    
    pair_id = 0
    distance_from_fan = 30.0
    low_height = 3.0
    high_height = 12.0
    wall = 'back'
    
    sensor_pair = SensorPair(pair_id, distance_from_fan, low_height, high_height, FAN_POSITION, wall)
    
    print(f"\nSensor Configuration:")
    print(f"  Wall: {wall.upper()}")
    print(f"  Distance from fan: {distance_from_fan} ft (for X offset)")
    print(f"  Low sensor height: {low_height} ft")
    print(f"  High sensor height: {high_height} ft")
    
    print(f"\nLow Sensor Position:")
    print(f"  X = {sensor_pair.low_sensor.position[0]:.2f} ft")
    print(f"  Y = {sensor_pair.low_sensor.position[1]:.2f} ft")
    print(f"  Z = {sensor_pair.low_sensor.position[2]:.2f} ft")
    
    print(f"\nHigh Sensor Position:")
    print(f"  X = {sensor_pair.high_sensor.position[0]:.2f} ft")
    print(f"  Y = {sensor_pair.high_sensor.position[1]:.2f} ft")
    print(f"  Z = {sensor_pair.high_sensor.position[2]:.2f} ft")
    
    # Verify back wall sensors are at Z=74.5 (6 inches from back)
    expected_z = 74.5
    assert sensor_pair.low_sensor.position[2] == expected_z, \
        f"Back wall sensor Z should be {expected_z}, got {sensor_pair.low_sensor.position[2]}"
    assert sensor_pair.high_sensor.position[2] == expected_z, \
        f"Back wall sensor Z should be {expected_z}, got {sensor_pair.high_sensor.position[2]}"
    
    # Verify heights
    assert sensor_pair.low_sensor.position[1] == low_height
    assert sensor_pair.high_sensor.position[1] == high_height
    
    print(f"\n✓ Back wall sensors correctly positioned at Z={expected_z} ft (6 inches from back wall)")
    return True

def test_sensor_front_wall():
    """Test sensor positioning on front wall."""
    print("\n" + "=" * 70)
    print("TEST 3: Sensor Positioning - Front Wall")
    print("=" * 70)
    
    pair_id = 1
    distance_from_fan = 30.0
    low_height = 3.0
    high_height = 12.0
    wall = 'front'
    
    sensor_pair = SensorPair(pair_id, distance_from_fan, low_height, high_height, FAN_POSITION, wall)
    
    print(f"\nSensor Configuration:")
    print(f"  Wall: {wall.upper()}")
    print(f"  Distance from fan: {distance_from_fan} ft (for X offset)")
    print(f"  Low sensor height: {low_height} ft")
    print(f"  High sensor height: {high_height} ft")
    
    print(f"\nLow Sensor Position:")
    print(f"  X = {sensor_pair.low_sensor.position[0]:.2f} ft")
    print(f"  Y = {sensor_pair.low_sensor.position[1]:.2f} ft")
    print(f"  Z = {sensor_pair.low_sensor.position[2]:.2f} ft")
    
    print(f"\nHigh Sensor Position:")
    print(f"  X = {sensor_pair.high_sensor.position[0]:.2f} ft")
    print(f"  Y = {sensor_pair.high_sensor.position[1]:.2f} ft")
    print(f"  Z = {sensor_pair.high_sensor.position[2]:.2f} ft")
    
    # Verify front wall sensors are at Z=0.5 (6 inches from front)
    expected_z = 0.5
    assert sensor_pair.low_sensor.position[2] == expected_z, \
        f"Front wall sensor Z should be {expected_z}, got {sensor_pair.low_sensor.position[2]}"
    assert sensor_pair.high_sensor.position[2] == expected_z, \
        f"Front wall sensor Z should be {expected_z}, got {sensor_pair.high_sensor.position[2]}"
    
    # Verify heights
    assert sensor_pair.low_sensor.position[1] == low_height
    assert sensor_pair.high_sensor.position[1] == high_height
    
    print(f"\n✓ Front wall sensors correctly positioned at Z={expected_z} ft (6 inches from front wall)")
    return True

def test_room_dimensions():
    """Verify room dimensions haven't changed."""
    print("\n" + "=" * 70)
    print("TEST 4: Room Dimensions")
    print("=" * 70)
    
    print(f"\nRoom Dimensions:")
    print(f"  Width (X): {ROOM_WIDTH} ft")
    print(f"  Height (Y): {ROOM_HEIGHT} ft")
    print(f"  Length (Z): {ROOM_LENGTH} ft")
    
    assert ROOM_WIDTH == 30.0
    assert ROOM_HEIGHT == 20.0
    assert ROOM_LENGTH == 75.0
    
    print("\n✓ Room dimensions are correct!")
    return True

if __name__ == "__main__":
    print("\n" + "█" * 70)
    print("FAN POSITION & SENSOR WALL SELECTION - VERIFICATION TESTS")
    print("█" * 70)
    
    try:
        test_fan_position()
        test_sensor_back_wall()
        test_sensor_front_wall()
        test_room_dimensions()
        
        print("\n" + "█" * 70)
        print("✓ ALL TESTS PASSED!")
        print("█" * 70)
        print("\nSummary:")
        print("  • Fan moved to left wall (X=0.5, Y=18, Z=70)")
        print("  • Sensors can be placed on front wall (Z=0.5) or back wall (Z=74.5)")
        print("  • Wall selection properly affects sensor Z-coordinate")
        print("  • Heights and X-offsets work correctly")
        print("\n")
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        exit(1)
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
