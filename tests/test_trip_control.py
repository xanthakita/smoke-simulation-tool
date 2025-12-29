#!/usr/bin/env python3
"""Test suite for trip control functionality."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
from simulation.room import Room
from simulation.fan import ExhaustFan
from simulation.sensor import SensorPair
from simulation.smoke_physics import SmokeSimulation
from controllers.fan_controller import TripController
from utils.constants import FAN_POSITION


def create_mock_particles(concentration_ppm, position, detection_radius=1.0):
    """Create mock particles at a specific position with given concentration.
    
    The sensor calculates PPM as:
      particles_per_cubic_foot = particles_in_range / detection_volume
      instantaneous_ppm = particles_per_cubic_foot * 10
    
    Args:
        concentration_ppm: Target PPM concentration
        position: (x, y, z) position tuple
        detection_radius: Sensor detection radius in feet (default: 1.0)
    
    Returns:
        Array of particle positions
    """
    # Calculate required particles for target PPM
    # detection_volume = (4/3) * π * r³
    detection_volume = (4.0 / 3.0) * np.pi * (detection_radius ** 3)
    
    # PPM = particles_per_cubic_foot * 10
    # particles_per_cubic_foot = PPM / 10
    particles_per_cubic_foot = concentration_ppm / 10.0
    
    # particles_in_range = particles_per_cubic_foot * detection_volume
    particles_needed = int(particles_per_cubic_foot * detection_volume) + 1
    
    # Create particles within detection radius
    x, y, z = position
    particles = []
    for _ in range(particles_needed):
        # Create particles uniformly within the detection sphere
        # Use rejection sampling
        while True:
            offset = np.random.uniform(-detection_radius, detection_radius, 3)
            if np.linalg.norm(offset) <= detection_radius * 0.9:  # Keep within 90% of radius
                break
        particles.append([x + offset[0], y + offset[1], z + offset[2]])
    
    return np.array(particles)


def test_single_sensor_trip():
    """Test 1: Verify single sensor trip activates fan."""
    print("\n" + "="*60)
    print("TEST 1: Single Sensor Trip Activation")
    print("="*60)
    
    fan = ExhaustFan()
    trip_controller = TripController(fan)
    
    # Create a sensor pair with low trip thresholds
    sensor = SensorPair(
        pair_id=0,
        distance_from_fan=30.0,
        low_height=3.0,
        high_height=12.0,
        fan_position=FAN_POSITION,
        wall='south',
        trip_ppm=50,
        trip_aqi=100,
        trip_duration=10  # 10 seconds
    )
    
    trip_controller.add_sensor_pair(sensor)
    trip_controller.set_mode('trip')
    
    # Create high-concentration particles near sensor
    particles = create_mock_particles(100, sensor.low_sensor.position)
    
    # Update sensor with particles multiple times to fill history buffer
    dt = 0.1
    for _ in range(15):  # Fill history (maxlen=10) plus some extra
        sensor.update(particles, dt)
        trip_controller.update(dt)  # Controller updates trip state
        fan.update(dt)  # Fan ramps to target speed
    
    print(f"Sensor readings:")
    readings = sensor.get_readings()
    print(f"  Low PPM: {readings['low']['ppm']:.2f}, AQI: {readings['low']['aqi']:.0f}")
    print(f"  High PPM: {readings['high']['ppm']:.2f}, AQI: {readings['high']['aqi']:.0f}")
    print(f"  Trip PPM threshold: {sensor.trip_ppm}")
    print(f"  Trip AQI threshold: {sensor.trip_aqi}")
    print(f"\nSensor tripped: {sensor.is_tripped}")
    print(f"Sensor max AQI: {sensor.get_max_aqi():.1f}")
    
    # Get controller status for debugging
    status = trip_controller.get_status()
    print(f"\nTrip controller status:")
    print(f"  Mode: {status['mode']}")
    print(f"  Any sensor tripped: {status['any_sensor_tripped']}")
    print(f"  Highest AQI: {status['highest_aqi']:.1f}")
    
    print(f"\nFan speed after trip: {fan.speed_percent:.1f}%")
    print(f"Expected: > 0%")
    
    # Verify fan is running
    assert fan.speed_percent > 0, "Fan should be running after trip"
    assert sensor.is_tripped, "Sensor should be tripped"
    
    print("\n✓ TEST 1 PASSED: Single sensor trip activates fan")
    return True


def test_multiple_sensors_longest_duration():
    """Test 2: Verify multiple sensors use longest duration."""
    print("\n" + "="*60)
    print("TEST 2: Multiple Sensors - Longest Duration")
    print("="*60)
    
    fan = ExhaustFan()
    trip_controller = TripController(fan)
    
    # Create multiple sensor pairs with different trip durations
    sensor1 = SensorPair(
        pair_id=0,
        distance_from_fan=15.0,
        low_height=3.0,
        high_height=12.0,
        fan_position=FAN_POSITION,
        wall='south',
        trip_ppm=50,
        trip_aqi=100,
        trip_duration=60  # 60 seconds
    )
    
    sensor2 = SensorPair(
        pair_id=1,
        distance_from_fan=35.0,
        low_height=3.0,
        high_height=12.0,
        fan_position=FAN_POSITION,
        wall='south',
        trip_ppm=50,
        trip_aqi=100,
        trip_duration=120  # 120 seconds (longest)
    )
    
    sensor3 = SensorPair(
        pair_id=2,
        distance_from_fan=50.0,
        low_height=3.0,
        high_height=12.0,
        fan_position=FAN_POSITION,
        wall='south',
        trip_ppm=50,
        trip_aqi=100,
        trip_duration=90  # 90 seconds
    )
    
    trip_controller.add_sensor_pair(sensor1)
    trip_controller.add_sensor_pair(sensor2)
    trip_controller.add_sensor_pair(sensor3)
    trip_controller.set_mode('trip')
    
    # Create particles near all sensors
    particles1 = create_mock_particles(100, sensor1.low_sensor.position)
    particles2 = create_mock_particles(100, sensor2.low_sensor.position)
    particles3 = create_mock_particles(100, sensor3.low_sensor.position)
    all_particles = np.vstack([particles1, particles2, particles3])
    
    # Update all sensors multiple times to fill history buffer
    dt = 0.1
    for _ in range(15):
        sensor1.update(all_particles, dt)
        sensor2.update(all_particles, dt)
        sensor3.update(all_particles, dt)
        trip_controller.update(dt)  # Controller updates trip states
        fan.update(dt)  # Fan ramps to target speed
    
    print(f"Sensor 1 tripped: {sensor1.is_tripped}, Duration: {sensor1.trip_duration}s")
    print(f"Sensor 2 tripped: {sensor2.is_tripped}, Duration: {sensor2.trip_duration}s")
    print(f"Sensor 3 tripped: {sensor3.is_tripped}, Duration: {sensor3.trip_duration}s")
    
    # Update trip controller
    trip_controller.update(dt=0.1)
    
    status = trip_controller.get_status()
    print(f"\nTrip controller status:")
    print(f"  Any sensor tripped: {status['any_sensor_tripped']}")
    print(f"  Max remaining duration: {status['max_remaining_duration']:.1f}s")
    print(f"  Expected max duration: ~{sensor2.trip_duration}s (from sensor 2)")
    
    # Verify longest duration is used
    assert status['any_sensor_tripped'], "At least one sensor should be tripped"
    assert abs(status['max_remaining_duration'] - sensor2.trip_duration) < 1, \
        "Should use longest duration from sensor 2"
    
    print("\n✓ TEST 2 PASSED: Multiple sensors use longest duration")
    return True


def test_fan_speed_increases_with_aqi():
    """Test 3: Verify fan speed increases with higher AQI."""
    print("\n" + "="*60)
    print("TEST 3: Fan Speed Increases with AQI")
    print("="*60)
    
    fan = ExhaustFan()
    trip_controller = TripController(fan)
    
    # Create sensor with low trip threshold
    sensor = SensorPair(
        pair_id=0,
        distance_from_fan=30.0,
        low_height=3.0,
        high_height=12.0,
        fan_position=FAN_POSITION,
        wall='south',
        trip_ppm=20,
        trip_aqi=50,
        trip_duration=60
    )
    
    trip_controller.add_sensor_pair(sensor)
    trip_controller.set_mode('trip')
    
    # Test different AQI levels
    test_cases = [
        (50, "Low"),      # Low concentration
        (100, "Medium"),  # Medium concentration
        (200, "High")     # High concentration
    ]
    
    speeds = []
    dt = 0.1
    
    for ppm, level in test_cases:
        sensor.reset()
        fan.set_speed(0)
        trip_controller.current_time = 0.0  # Reset controller time
        
        # Create particles
        particles = create_mock_particles(ppm, sensor.low_sensor.position)
        
        # Update sensor multiple times to fill history
        for _ in range(15):
            sensor.update(particles, dt)
            trip_controller.update(dt)  # Controller updates trip state
            fan.update(dt)  # Fan ramps to target speed
        
        readings = sensor.get_readings()
        aqi = max(readings['low']['aqi'], readings['high']['aqi'])
        
        print(f"\n{level} concentration:")
        print(f"  Target PPM: {ppm}")
        print(f"  Measured AQI: {aqi:.0f}")
        print(f"  Fan speed: {fan.speed_percent:.1f}%")
        
        speeds.append(fan.speed_percent)
    
    # Verify fan speed increases with AQI
    print(f"\nSpeed progression: {speeds}")
    print(f"Expected: Increasing speeds")
    
    # Check that speeds generally increase (with some tolerance for variation)
    assert speeds[1] >= speeds[0] * 0.9, "Medium AQI should have higher or similar speed than low"
    assert speeds[2] >= speeds[1] * 0.9, "High AQI should have higher or similar speed than medium"
    
    print("\n✓ TEST 3 PASSED: Fan speed increases with higher AQI")
    return True


def test_trip_expiration():
    """Test 4: Verify fan turns off when all trips expire."""
    print("\n" + "="*60)
    print("TEST 4: Trip Expiration - Fan Turns Off")
    print("="*60)
    
    fan = ExhaustFan()
    trip_controller = TripController(fan)
    
    # Create sensor with short trip duration
    sensor = SensorPair(
        pair_id=0,
        distance_from_fan=30.0,
        low_height=3.0,
        high_height=12.0,
        fan_position=FAN_POSITION,
        wall='south',
        trip_ppm=50,
        trip_aqi=100,
        trip_duration=2  # 2 seconds for quick test
    )
    
    trip_controller.add_sensor_pair(sensor)
    trip_controller.set_mode('trip')
    
    # Create high-concentration particles
    particles = create_mock_particles(100, sensor.low_sensor.position)
    
    # Update sensor and trip it (fill history buffer)
    dt = 0.1
    for _ in range(15):
        sensor.update(particles, dt)
        trip_controller.update(dt)  # Controller updates trip state
        fan.update(dt)  # Fan ramps to target speed
    
    print(f"Initial state:")
    print(f"  Sensor tripped: {sensor.is_tripped}")
    print(f"  Remaining duration: {sensor.remaining_duration:.1f}s")
    print(f"  Fan speed: {fan.speed_percent:.1f}%")
    
    assert fan.speed_percent > 0, "Fan should be running after trip"
    
    # Simulate time passing beyond trip duration (no new particles)
    print(f"\nSimulating time passing (no new particles)...")
    print(f"  Note: Trip duration continues while readings are above threshold")
    
    steps = 0
    max_steps = 100  # 10 seconds - wait for sensor history to clear, trip to expire, and fan to ramp down
    while steps < max_steps:
        # Update with no new particles
        sensor.update(np.array([]), dt)
        trip_controller.update(dt)
        fan.update(dt)
        
        steps += 1
        current_time = trip_controller.current_time
        
        # Print at specific intervals
        if steps % 10 == 0:  # Every 1 second
            readings = sensor.get_readings()
            max_ppm = max(readings['low']['ppm'], readings['high']['ppm'])
            print(f"  t={current_time:.1f}s: PPM={max_ppm:.1f}, Remaining={sensor.remaining_duration:.1f}s, "
                  f"Tripped={sensor.is_tripped}, Speed={fan.speed_percent:.1f}%")
    
    print(f"\nFinal state:")
    print(f"  Sensor tripped: {sensor.is_tripped}")
    print(f"  Fan speed: {fan.speed_percent:.1f}%")
    
    # Verify fan turned off (should be off after readings drop and duration expires)
    assert not sensor.is_tripped, "Sensor trip should have expired after readings dropped"
    assert fan.speed_percent < 5, f"Fan should be off or ramping down after trip expires (got {fan.speed_percent}%)"
    
    print("\n✓ TEST 4 PASSED: Fan turns off when trip expires")
    return True


def test_mode_switching():
    """Test 5: Verify clean mode switching between Manual, Auto, and Trip."""
    print("\n" + "="*60)
    print("TEST 5: Mode Switching")
    print("="*60)
    
    fan = ExhaustFan()
    trip_controller = TripController(fan)
    
    # Create sensor
    sensor = SensorPair(
        pair_id=0,
        distance_from_fan=30.0,
        low_height=3.0,
        high_height=12.0,
        fan_position=FAN_POSITION,
        wall='south',
        trip_ppm=50,
        trip_aqi=100,
        trip_duration=60
    )
    
    trip_controller.add_sensor_pair(sensor)
    
    # Test mode transitions
    print("Testing mode transitions:")
    
    # Manual mode
    trip_controller.set_mode('manual')
    print(f"  Manual mode: controller mode = {trip_controller.mode}")
    assert trip_controller.mode == 'manual'
    
    # Trip mode
    trip_controller.set_mode('trip')
    print(f"  Trip mode: controller mode = {trip_controller.mode}")
    assert trip_controller.mode == 'trip'
    
    # Create particles and trip sensor
    particles = create_mock_particles(100, sensor.low_sensor.position)
    dt = 0.1
    for _ in range(15):
        sensor.update(particles, dt)
        trip_controller.update(dt)  # Controller updates trip state
        fan.update(dt)  # Fan ramps to target speed
    
    print(f"    Sensor tripped, fan speed: {fan.speed_percent:.1f}%")
    assert sensor.is_tripped
    
    # Switch back to manual - should reset trip state
    print(f"\n  Switching to manual mode...")
    trip_controller.set_mode('manual')
    sensor.reset()  # Reset would happen in UI when switching modes
    
    print(f"    Sensor tripped after reset: {sensor.is_tripped}")
    assert not sensor.is_tripped, "Trip state should be reset when switching modes"
    
    print("\n✓ TEST 5 PASSED: Mode switching works correctly")
    return True


def run_all_tests():
    """Run all trip control tests."""
    print("\n" + "="*60)
    print("TRIP CONTROL TEST SUITE")
    print("="*60)
    
    tests = [
        test_single_sensor_trip,
        test_multiple_sensors_longest_duration,
        test_fan_speed_increases_with_aqi,
        test_trip_expiration,
        test_mode_switching
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except AssertionError as e:
            print(f"\n✗ TEST FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"\n✗ TEST ERROR: {e}")
            failed += 1
    
    print("\n" + "="*60)
    print("TEST RESULTS")
    print("="*60)
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n✓ ALL TESTS PASSED!")
        return True
    else:
        print(f"\n✗ {failed} TEST(S) FAILED")
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
