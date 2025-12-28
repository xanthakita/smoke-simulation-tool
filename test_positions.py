#!/usr/bin/env python3
"""Test script to verify fan and sensor positions."""

import sys
import numpy as np

# Add project root to path
sys.path.insert(0, '/home/ubuntu/github_repos/smoke-simulation-tool')

from utils.constants import FAN_POSITION, ROOM_WIDTH, ROOM_LENGTH, ROOM_HEIGHT
from simulation.sensor import SensorPair


def test_fan_position():
    """Verify fan position is correct."""
    print("=" * 60)
    print("FAN POSITION TEST")
    print("=" * 60)
    print(f"Expected Fan Position: X=0.5, Y=17.5, Z=5.0")
    print(f"Actual Fan Position:   X={FAN_POSITION[0]}, Y={FAN_POSITION[1]}, Z={FAN_POSITION[2]}")
    
    # Check each coordinate
    assert np.isclose(FAN_POSITION[0], 0.5), f"Fan X position should be 0.5, got {FAN_POSITION[0]}"
    assert np.isclose(FAN_POSITION[1], 17.5), f"Fan Y position should be 17.5, got {FAN_POSITION[1]}"
    assert np.isclose(FAN_POSITION[2], 5.0), f"Fan Z position should be 5.0, got {FAN_POSITION[2]}"
    
    print("\n✅ Fan position is correct!")
    print(f"   - On LEFT WALL (X={FAN_POSITION[0]} ft, 6 inches from edge)")
    print(f"   - Height: {FAN_POSITION[1]} ft (2.5 ft from {ROOM_HEIGHT} ft ceiling)")
    print(f"   - Distance from FRONT WALL: {FAN_POSITION[2]} ft")
    print()


def test_sensor_positions():
    """Verify sensor positions for both walls."""
    print("=" * 60)
    print("SENSOR POSITION TEST")
    print("=" * 60)
    
    # Test Back Wall sensor
    print("\n1. Testing BACK WALL sensor placement:")
    back_sensor = SensorPair(0, 30.0, 3.0, 12.0, FAN_POSITION, wall='back')
    back_low_z = back_sensor.low_sensor.position[2]
    back_high_z = back_sensor.high_sensor.position[2]
    
    print(f"   Expected Z position: 74.5 ft (6 inches from back wall)")
    print(f"   Actual Low Sensor Z:  {back_low_z} ft")
    print(f"   Actual High Sensor Z: {back_high_z} ft")
    
    assert np.isclose(back_low_z, 74.5), f"Back wall sensor should be at Z=74.5, got {back_low_z}"
    assert np.isclose(back_high_z, 74.5), f"Back wall sensor should be at Z=74.5, got {back_high_z}"
    print("   ✅ Back wall sensors positioned correctly!")
    
    # Test Front Wall sensor
    print("\n2. Testing FRONT WALL sensor placement:")
    front_sensor = SensorPair(1, 30.0, 3.0, 12.0, FAN_POSITION, wall='front')
    front_low_z = front_sensor.low_sensor.position[2]
    front_high_z = front_sensor.high_sensor.position[2]
    
    print(f"   Expected Z position: 0.5 ft (6 inches from front wall)")
    print(f"   Actual Low Sensor Z:  {front_low_z} ft")
    print(f"   Actual High Sensor Z: {front_high_z} ft")
    
    assert np.isclose(front_low_z, 0.5), f"Front wall sensor should be at Z=0.5, got {front_low_z}"
    assert np.isclose(front_high_z, 0.5), f"Front wall sensor should be at Z=0.5, got {front_high_z}"
    print("   ✅ Front wall sensors positioned correctly!")
    
    # Test height positioning
    print("\n3. Testing sensor HEIGHT positioning:")
    print(f"   Low sensor height:  {back_sensor.low_sensor.position[1]} ft (expected 3.0 ft)")
    print(f"   High sensor height: {back_sensor.high_sensor.position[1]} ft (expected 12.0 ft)")
    
    assert np.isclose(back_sensor.low_sensor.position[1], 3.0), "Low sensor height incorrect"
    assert np.isclose(back_sensor.high_sensor.position[1], 12.0), "High sensor height incorrect"
    print("   ✅ Sensor heights correct!")
    print()


def test_room_dimensions():
    """Verify room dimensions."""
    print("=" * 60)
    print("ROOM DIMENSIONS")
    print("=" * 60)
    print(f"Room Width (X):  {ROOM_WIDTH} ft")
    print(f"Room Height (Y): {ROOM_HEIGHT} ft")
    print(f"Room Length (Z): {ROOM_LENGTH} ft")
    print()


def main():
    """Run all tests."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 12 + "FAN AND SENSOR POSITION VERIFICATION" + " " * 10 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    try:
        test_room_dimensions()
        test_fan_position()
        test_sensor_positions()
        
        print("=" * 60)
        print("ALL TESTS PASSED! ✅")
        print("=" * 60)
        print("\nSummary:")
        print("  • Fan is on LEFT WALL at X=0.5, Y=17.5, Z=5.0")
        print("  • Fan is 5 feet from FRONT wall (not back)")
        print("  • Back wall sensors are at Z=74.5 ft")
        print("  • Front wall sensors are at Z=0.5 ft")
        print("  • Sensor wall selection is working correctly")
        print()
        
    except AssertionError as e:
        print("\n" + "=" * 60)
        print("❌ TEST FAILED!")
        print("=" * 60)
        print(f"Error: {e}")
        print()
        sys.exit(1)


if __name__ == "__main__":
    main()
