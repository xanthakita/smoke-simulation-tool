#!/usr/bin/env python3
"""Test script to verify coordinate remapping in 3D visualization."""

import sys
import numpy as np
from PyQt5.QtWidgets import QApplication
from simulation.room import Room
from simulation.fan import ExhaustFan
from simulation.sensor import SensorPair
from simulation.smoke_physics import SmokeSimulation
from utils.constants import FAN_POSITION, ROOM_WIDTH, ROOM_LENGTH, ROOM_HEIGHT
from visualization.renderer_3d import Renderer3D


def print_coordinate_info():
    """Print information about the coordinate system."""
    print("=" * 80)
    print("COORDINATE REMAPPING VERIFICATION")
    print("=" * 80)
    print("\nROOM DIMENSIONS (from constants):")
    print(f"  ROOM_WIDTH  = {ROOM_WIDTH} ft")
    print(f"  ROOM_LENGTH = {ROOM_LENGTH} ft")
    print(f"  ROOM_HEIGHT = {ROOM_HEIGHT} ft")
    
    print("\nDATA STORAGE FORMAT:")
    print("  All positions stored as: [Length, Width, Height]")
    print(f"  Index 0 (Length): 0-{ROOM_LENGTH} ft")
    print(f"  Index 1 (Width):  0-{ROOM_WIDTH} ft")
    print(f"  Index 2 (Height): 0-{ROOM_HEIGHT} ft")
    
    print("\nDISPLAY MAPPING (matplotlib axes):")
    print("  X-axis (Width, horizontal):  0-30 ft ← data[2] (Height)")
    print("  Y-axis (Height, VERTICAL):   0-20 ft ← data[0] (Length)")
    print("  Z-axis (Length, depth):      0-75 ft ← data[1] (Width)")
    
    print("\nFAN POSITION:")
    print(f"  In DATA: {FAN_POSITION} = [Length, Width, Height]")
    print(f"  Length={FAN_POSITION[0]} → Display Y (Height) = {FAN_POSITION[0]} ft")
    print(f"  Width={FAN_POSITION[1]} → Display Z (Length) = {FAN_POSITION[1]} ft")
    print(f"  Height={FAN_POSITION[2]} → Display X (Width) = {FAN_POSITION[2]} ft")
    print(f"  So fan displays at: X={FAN_POSITION[2]}, Y={FAN_POSITION[0]}, Z={FAN_POSITION[1]}")
    
    print("\nEXPECTED RESULT:")
    print("  ✓ Room appears upright (not rotated on side)")
    print("  ✓ Y-axis is vertical (Height: 0-20 ft)")
    print("  ✓ X-axis is horizontal (Width: 0-30 ft)")
    print("  ✓ Z-axis is depth (Length: 0-75 ft)")
    print("  ✓ Fan on back wall at correct height")
    print("  ✓ Smoke rises vertically along Y-axis")
    print("=" * 80)


def test_coordinate_mapping():
    """Test the coordinate remapping in visualization."""
    print_coordinate_info()
    
    print("\n\nInitializing simulation components...")
    
    # Create simulation objects
    room = Room()
    fan = ExhaustFan()
    smoke_sim = SmokeSimulation(room, fan)
    
    # Create a few sensor pairs for testing
    sensor_pairs = []
    for i in range(2):
        sensor = SensorPair(
            pair_id=i,
            distance_from_fan=20.0 + i * 15.0,
            low_height=5.0,
            high_height=15.0,
            fan_position=FAN_POSITION
        )
        sensor_pairs.append(sensor)
    
    # Set up some smokers to generate particles
    smoke_sim.set_num_smokers(4)
    
    # Run simulation for a bit to generate particles
    print("Generating test particles...")
    for _ in range(50):  # 5 seconds of simulation
        smoke_sim.update(0.1)
    
    particles = smoke_sim.get_particles()
    print(f"Generated {len(particles)} particles")
    
    if len(particles) > 0:
        print("\nPARTICLE COORDINATE ANALYSIS:")
        print(f"  Data column 0 (Length): min={particles[:, 0].min():.1f}, max={particles[:, 0].max():.1f} ft")
        print(f"  Data column 1 (Width):  min={particles[:, 1].min():.1f}, max={particles[:, 1].max():.1f} ft")
        print(f"  Data column 2 (Height): min={particles[:, 2].min():.1f}, max={particles[:, 2].max():.1f} ft")
        
        print("\n  After remapping for display:")
        print(f"  X (Width) from data[2]:  min={particles[:, 2].min():.1f}, max={particles[:, 2].max():.1f} ft")
        print(f"  Y (Height) from data[0]: min={particles[:, 0].min():.1f}, max={particles[:, 0].max():.1f} ft")
        print(f"  Z (Length) from data[1]: min={particles[:, 1].min():.1f}, max={particles[:, 1].max():.1f} ft")
    
    print("\nSENSOR POSITIONS:")
    for i, pair in enumerate(sensor_pairs):
        low_pos = pair.low_sensor.position
        high_pos = pair.high_sensor.position
        print(f"  Pair {i}:")
        print(f"    Low sensor DATA:  [{low_pos[0]:.1f}, {low_pos[1]:.1f}, {low_pos[2]:.1f}]")
        print(f"    Low sensor DISPLAY: X={low_pos[2]:.1f}, Y={low_pos[0]:.1f}, Z={low_pos[1]:.1f}")
        print(f"    High sensor DATA:  [{high_pos[0]:.1f}, {high_pos[1]:.1f}, {high_pos[2]:.1f}]")
        print(f"    High sensor DISPLAY: X={high_pos[2]:.1f}, Y={high_pos[0]:.1f}, Z={high_pos[1]:.1f}")
    
    print("\n" + "=" * 80)
    print("Testing visualization rendering...")
    print("=" * 80)
    
    # Create Qt application and renderer
    app = QApplication(sys.argv)
    renderer = Renderer3D()
    renderer.set_simulation_refs(smoke_sim, fan, sensor_pairs)
    renderer.update()
    renderer.resize(1200, 900)
    renderer.show()
    
    print("\n✓ Visualization window opened!")
    print("✓ Please verify:")
    print("  1. Room appears upright (not rotated)")
    print("  2. Y-axis is vertical with range 0-20 ft (Height)")
    print("  3. X-axis is horizontal with range 0-30 ft (Width)")
    print("  4. Z-axis shows depth with range 0-75 ft (Length)")
    print("  5. Fan is on back wall (Z=75) at correct height")
    print("  6. Smoke particles appear at correct positions")
    print("\nClose the window to exit.")
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    test_coordinate_mapping()
