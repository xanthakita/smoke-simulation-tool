#!/usr/bin/env python3
"""Test script for height-dependent smoke physics."""

import sys
import numpy as np
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, '/home/ubuntu/smoke_simulation_tool')

from simulation.smoke_physics import SmokeSimulation
from simulation.room import Room
from simulation.fan import ExhaustFan
from utils.constants import ROOM_WIDTH, ROOM_LENGTH, ROOM_HEIGHT, FAN_POSITION


def test_height_dependent_physics():
    """Test the height-dependent smoke physics implementation."""
    
    print("="*80)
    print("TESTING HEIGHT-DEPENDENT SMOKE PHYSICS")
    print("="*80)
    print(f"Start time: {datetime.now().strftime('%H:%M:%S')}\n")
    
    # Create simulation components
    room = Room()
    fan = ExhaustFan()
    fan.set_speed(50.0)
    smoke_sim = SmokeSimulation(room, fan)
    
    # Set up 4 cigars for testing
    num_cigars = 4
    smoke_sim.set_num_smokers(num_cigars)
    
    print(f"✓ Created simulation with {num_cigars} cigars")
    print(f"✓ Room dimensions: {ROOM_WIDTH} x {ROOM_LENGTH} x {ROOM_HEIGHT} feet")
    print(f"✓ Fan position: {FAN_POSITION} at 50% speed\n")
    
    # Run simulation for 2 minutes (120 seconds) of simulated time
    sim_duration = 120.0  # seconds
    time_step = 0.1  # seconds
    steps = int(sim_duration / time_step)
    
    print(f"Running simulation for {sim_duration} seconds ({steps} steps)...\n")
    
    # Track some statistics during simulation
    max_particles = 0
    height_snapshots = []
    
    for step in range(steps):
        smoke_sim.update(time_step)
        
        current_particles = smoke_sim.get_particle_count()
        max_particles = max(max_particles, current_particles)
        
        # Take snapshots at specific times
        if smoke_sim.time in [30.0, 60.0, 90.0, 120.0]:
            dist = smoke_sim.get_height_distribution()
            height_snapshots.append((smoke_sim.time, dist))
    
    print("\n" + "="*80)
    print("SIMULATION COMPLETE - ANALYZING RESULTS")
    print("="*80)
    
    # Get final statistics
    final_stats = smoke_sim.get_statistics()
    final_dist = smoke_sim.get_height_distribution()
    
    print(f"\n📈 FINAL STATISTICS:")
    print(f"   Total particles generated: {final_stats['particles_generated']}")
    print(f"   Total particles removed: {final_stats['particles_removed']}")
    print(f"   Current particles: {final_stats['particle_count']}")
    print(f"   Maximum particles: {max_particles}")
    print(f"   Average PPM: {final_stats['avg_ppm']:.2f}")
    print(f"   Average Clarity: {final_stats['avg_clarity']:.2f}%")
    
    # Print final height distribution
    smoke_sim.print_height_distribution()
    
    # Analyze stratification behavior
    print("\n" + "="*80)
    print("STRATIFICATION ANALYSIS")
    print("="*80)
    
    total = final_dist['total']
    if total > 0:
        pct_hover = (final_dist['zone_4_8'] / total) * 100
        pct_upper = (final_dist['zone_14_18'] / total) * 100
        pct_ceiling = (final_dist['zone_18_plus'] / total) * 100
        
        print(f"\n✓ HOVER ZONE (4-8 ft): {pct_hover:.1f}% of particles")
        if pct_hover > 15:
            print("  ✅ GOOD - Significant smoke hovering in this zone")
        else:
            print("  ⚠️  WARNING - Less hovering than expected")
        
        print(f"\n✓ UPPER ZONE (14-18 ft): {pct_upper:.1f}% of particles")
        if 10 < pct_upper < 30:
            print("  ✅ GOOD - Smoke gradually reaching upper zone")
        elif pct_upper > 30:
            print("  ⚠️  WARNING - Too much smoke in upper zone")
        else:
            print("  ⚠️  WARNING - Not enough smoke reaching upper zone")
        
        print(f"\n✓ NEAR CEILING (18+ ft): {pct_ceiling:.1f}% of particles")
        if pct_ceiling < 10:
            print("  ✅ GOOD - Smoke stratifying, not rushing to ceiling")
        else:
            print("  ⚠️  WARNING - Too much smoke at ceiling")
    
    # Test horizontal spread
    print("\n" + "="*80)
    print("HORIZONTAL SPREAD ANALYSIS")
    print("="*80)
    
    if smoke_sim.get_particle_count() > 0:
        positions = smoke_sim.get_particles()
        
        # Calculate spread from each cigar position
        cigar_positions = smoke_sim.smoker_positions
        
        for i, cigar_pos in enumerate(cigar_positions):
            # Calculate distances in X-Z plane
            horizontal_distances = np.sqrt(
                (positions[:, 0] - cigar_pos[0])**2 + 
                (positions[:, 2] - cigar_pos[2])**2
            )
            
            # Find particles within 20 feet
            within_20ft = np.sum(horizontal_distances <= 20.0)
            max_spread = np.max(horizontal_distances) if len(horizontal_distances) > 0 else 0
            avg_spread = np.mean(horizontal_distances) if len(horizontal_distances) > 0 else 0
            
            print(f"\n✓ Cigar #{i+1} at ({cigar_pos[0]:.1f}, {cigar_pos[1]:.1f}, {cigar_pos[2]:.1f}):")
            print(f"   Maximum spread: {max_spread:.1f} feet")
            print(f"   Average spread: {avg_spread:.1f} feet")
            
            if max_spread >= 15.0:
                print(f"   ✅ GOOD - Spread reaches 15-20 feet target")
            else:
                print(f"   ⚠️  WARNING - Spread less than 15 feet")
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)
    print(f"End time: {datetime.now().strftime('%H:%M:%S')}")
    
    return True


if __name__ == "__main__":
    try:
        success = test_height_dependent_physics()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
