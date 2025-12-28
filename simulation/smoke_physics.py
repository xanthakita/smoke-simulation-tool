"""Smoke physics simulation engine with particle system."""

import numpy as np
from utils.constants import (
    TIME_STEP, GRAVITY, BUOYANCY_FACTOR, DIFFUSION_COEFFICIENT,
    PARTICLES_PER_CIGAR_PER_SECOND, MAX_PARTICLES, SMOKER_HEIGHT,
    ROOM_WIDTH, ROOM_LENGTH, ROOM_HEIGHT
)
from simulation.cigar_model import CigarManager


class SmokeParticle:
    """Represents a smoke particle in the simulation."""
    
    def __init__(self, position, velocity=None, age=0.0):
        """Initialize a smoke particle.
        
        Args:
            position: numpy array [x, y, z]
            velocity: numpy array [vx, vy, vz] (optional)
            age: age of particle in seconds
        """
        self.position = np.array(position, dtype=float)
        self.velocity = np.array(velocity if velocity is not None else [0, 0, 0], dtype=float)
        self.age = age
        self.lifetime = 300.0  # Particles last 5 minutes before removal


class SmokeSimulation:
    """Main smoke physics simulation engine."""
    
    def __init__(self, room, fan):
        """Initialize smoke simulation.
        
        Args:
            room: Room object
            fan: ExhaustFan object
        """
        self.room = room
        self.fan = fan
        
        # Particle storage (using numpy arrays for efficiency)
        self.particles_positions = np.zeros((0, 3), dtype=float)
        self.particles_velocities = np.zeros((0, 3), dtype=float)
        self.particles_ages = np.zeros(0, dtype=float)
        
        # Simulation state
        self.time = 0.0
        self.num_smokers = 0
        self.smoker_positions = np.zeros((0, 3), dtype=float)
        self.particle_generation_rate = PARTICLES_PER_CIGAR_PER_SECOND
        
        # Cigar manager for realistic smoking behavior
        self.cigar_manager = CigarManager(room)
        
        # Performance tracking
        self.particles_generated = 0
        self.particles_removed = 0
        
        # Accumulator for fractional particles
        self.particle_accumulator = 0.0
        
        # Debug tracking for height distribution
        self.last_height_print_time = 0.0
        self.height_print_interval = 30.0  # Print every 30 seconds
        
    def set_num_smokers(self, num_smokers):
        """Set number of active smokers.
        
        Args:
            num_smokers: Number of smokers in the room
        """
        self.num_smokers = num_smokers
        self.smoker_positions = self.room.generate_smoker_positions(num_smokers, SMOKER_HEIGHT)
        
        # Initialize cigars for each smoker
        self.cigar_manager.set_num_smokers(num_smokers, self.smoker_positions)
    
    def generate_particles(self, dt):
        """Generate new smoke particles from smokers.
        
        Args:
            dt: Time step in seconds
        """
        if self.num_smokers == 0:
            return
        
        # Get smoke sources from cigar manager
        smoke_sources = self.cigar_manager.get_smoke_sources()
        
        if len(smoke_sources) == 0:
            return
        
        # Generate particles from each active cigar based on its current rate
        new_positions_list = []
        new_velocities_list = []
        
        for position, rate in smoke_sources:
            # Calculate particles to generate from this cigar
            particles_from_cigar = rate * dt
            self.particle_accumulator += particles_from_cigar
            
            num_particles = int(particles_from_cigar)
            
            if num_particles > 0:
                # Check if we're at max capacity
                current_count = len(self.particles_positions) + len(new_positions_list)
                if current_count + num_particles > MAX_PARTICLES:
                    num_particles = MAX_PARTICLES - current_count
                    if num_particles <= 0:
                        break
                
                # Generate particles at this cigar's position
                cigar_positions = np.tile(position, (num_particles, 1))
                
                # Add random offset to positions for initial spread
                # Much larger horizontal spread for realistic 15-20 feet dispersion
                position_offset = np.random.normal(0, 0.8, size=(num_particles, 3))
                position_offset[:, 1] *= 0.3  # Less vertical spread
                cigar_positions += position_offset
                
                # Initial velocity with VERY STRONG horizontal components
                # Smoke should spread out in a wide cone/plume shape (15-20 feet)
                cigar_velocities = np.zeros((num_particles, 3))
                
                # Very strong horizontal velocities (X and Z) for wide spread
                cigar_velocities[:, 0] = np.random.normal(0, 2.5, size=num_particles)
                cigar_velocities[:, 2] = np.random.normal(0, 2.5, size=num_particles)
                
                # Moderate upward velocity
                cigar_velocities[:, 1] = np.random.uniform(0.5, 2.0, size=num_particles)
                
                new_positions_list.append(cigar_positions)
                new_velocities_list.append(cigar_velocities)
        
        # Accumulator management
        accumulated_int = int(self.particle_accumulator)
        self.particle_accumulator -= accumulated_int
        
        if len(new_positions_list) == 0:
            return
        
        # Combine all new particles
        new_positions = np.vstack(new_positions_list)
        new_velocities = np.vstack(new_velocities_list)
        new_ages = np.zeros(len(new_positions))
        
        # Append to existing arrays
        self.particles_positions = np.vstack([self.particles_positions, new_positions])
        self.particles_velocities = np.vstack([self.particles_velocities, new_velocities])
        self.particles_ages = np.concatenate([self.particles_ages, new_ages])
        
        self.particles_generated += len(new_positions)
    
    def _calculate_height_dependent_buoyancy(self, heights):
        """Calculate height-dependent buoyancy factors based on Y-coordinate.
        
        Creates realistic stratification zones:
        - 0-4 feet: Moderate buoyancy (1.0x - smoke rises from source)
        - 4-8 feet: Very low buoyancy (0.05x - HOVER ZONE, smoke lingers)
        - 8-14 feet: Weak buoyancy (0.20x - slow gradual rise)
        - 14-18 feet: Very weak buoyancy (0.08x - reaches slowly)
        - Above 18 feet: Minimal/zero buoyancy (0.02x - rarely reaches ceiling)
        
        Args:
            heights: numpy array of Y-coordinates
            
        Returns:
            numpy array of buoyancy multipliers for each particle
        """
        buoyancy_multipliers = np.ones_like(heights)
        
        # Zone 1: 0-4 feet - Moderate buoyancy (1.0x)
        # Smoke rises from cigar
        mask_zone1 = heights < 4.0
        buoyancy_multipliers[mask_zone1] = 1.0
        
        # Zone 2: 4-8 feet - Very low buoyancy (0.05x) - HOVER ZONE
        # Smoke hovers and lingers here (reduced from 0.1 to 0.05)
        mask_zone2 = (heights >= 4.0) & (heights < 8.0)
        buoyancy_multipliers[mask_zone2] = 0.05
        
        # Zone 3: 8-14 feet - Weak buoyancy (0.20x)
        # Slow gradual rise (adjusted to 0.20 for better upper zone reach)
        mask_zone3 = (heights >= 8.0) & (heights < 14.0)
        buoyancy_multipliers[mask_zone3] = 0.20
        
        # Zone 4: 14-18 feet - Very weak buoyancy (0.08x)
        # Smoke reaches this range slowly (reduced from 0.15 to 0.08)
        mask_zone4 = (heights >= 14.0) & (heights < 18.0)
        buoyancy_multipliers[mask_zone4] = 0.08
        
        # Zone 5: Above 18 feet - Minimal/zero buoyancy (0.02x)
        # Smoke rarely reaches ceiling (reduced from 0.05 to 0.02)
        mask_zone5 = heights >= 18.0
        buoyancy_multipliers[mask_zone5] = 0.02
        
        return buoyancy_multipliers
    
    def _calculate_height_dependent_vertical_damping(self, heights):
        """Calculate height-dependent vertical velocity damping.
        
        Damping increases with height to slow down smoke rise and create hovering effect.
        Lower heights have less damping (smoke rises), higher heights have more damping (smoke slows).
        
        Args:
            heights: numpy array of Y-coordinates
            
        Returns:
            numpy array of damping factors for vertical velocity
        """
        damping_factors = np.ones_like(heights)
        
        # Zone 1: 0-4 feet - Low damping (0.93) - smoke rises freely
        mask_zone1 = heights < 4.0
        damping_factors[mask_zone1] = 0.93
        
        # Zone 2: 4-8 feet - High damping (0.75) - HOVER ZONE
        # Strong damping makes smoke slow down and hover (increased from 0.80)
        mask_zone2 = (heights >= 4.0) & (heights < 8.0)
        damping_factors[mask_zone2] = 0.75
        
        # Zone 3: 8-14 feet - Very high damping (0.70)
        # Strong slowdown of rise from hover zone (increased from 0.85)
        mask_zone3 = (heights >= 8.0) & (heights < 14.0)
        damping_factors[mask_zone3] = 0.70
        
        # Zone 4: 14-18 feet - Extreme damping (0.60)
        # Makes it much harder to reach this range (increased from 0.75)
        mask_zone4 = (heights >= 14.0) & (heights < 18.0)
        damping_factors[mask_zone4] = 0.60
        
        # Zone 5: Above 18 feet - Maximum damping (0.50)
        # Strongly prevents smoke from rushing to ceiling (increased from 0.70)
        mask_zone5 = heights >= 18.0
        damping_factors[mask_zone5] = 0.50
        
        return damping_factors
    
    def apply_physics(self, dt):
        """Apply physics forces to all particles.
        
        Args:
            dt: Time step in seconds
        """
        if len(self.particles_positions) == 0:
            return
        
        # Get particle heights (Y-coordinates)
        heights = self.particles_positions[:, 1]
        
        # 1. Height-Dependent Buoyancy (upward force due to temperature difference)
        # Smoke rises with varying strength depending on height
        buoyancy = np.zeros_like(self.particles_velocities)
        
        # Base buoyancy force
        base_buoyancy = BUOYANCY_FACTOR * GRAVITY
        
        # Apply height-dependent buoyancy multipliers
        height_multipliers = self._calculate_height_dependent_buoyancy(heights)
        buoyancy[:, 1] = base_buoyancy * height_multipliers
        
        # Reduce buoyancy for older particles (as they cool and equilibrate)
        # But never apply downward force - smoke doesn't fall
        age_factor = np.clip(1.0 - (self.particles_ages / 600.0), 0.3, 1.0)  # Keep 30% buoyancy even when old
        buoyancy[:, 1] *= age_factor
        
        # 2. Diffusion (random walk for spreading)
        # Very strong horizontal diffusion to model air currents and achieve 15-20 feet spread
        diffusion = np.random.normal(0, DIFFUSION_COEFFICIENT, size=self.particles_velocities.shape)
        # Significantly increase horizontal diffusion for realistic wide spread
        diffusion[:, 0] *= 3.5  # X-axis diffusion (increased from 2.0)
        diffusion[:, 2] *= 3.5  # Z-axis diffusion (increased from 2.0)
        # Reduce vertical diffusion to keep smoke more stable at its level
        diffusion[:, 1] *= 0.15  # Further reduced to encourage horizontal spread
        
        # 3. Fan suction (advection toward fan)
        fan_velocities = self.fan.calculate_velocity_field(self.particles_positions)
        
        # NOTE: No gravity applied to smoke particles
        # Smoke does NOT fall - it lingers and gradually rises
        
        # Combine forces
        acceleration = buoyancy + diffusion + fan_velocities
        
        # Update velocities
        self.particles_velocities += acceleration * dt
        
        # Apply height-dependent damping for realistic smoke behavior
        # Horizontal damping stays moderate to allow spread
        horizontal_damping = 0.92
        self.particles_velocities[:, 0] *= horizontal_damping
        self.particles_velocities[:, 2] *= horizontal_damping
        
        # Vertical damping increases with height to slow down smoke rise
        # This creates the hovering effect and prevents rushing to ceiling
        vertical_damping = self._calculate_height_dependent_vertical_damping(heights)
        self.particles_velocities[:, 1] *= vertical_damping
        
        # Update positions
        self.particles_positions += self.particles_velocities * dt
        
        # Boundary conditions - particles bounce off walls and ceiling/floor
        self._apply_boundary_conditions()
        
        # Age particles
        self.particles_ages += dt
    
    def _apply_boundary_conditions(self):
        """Apply boundary conditions to keep particles in room."""
        # X boundaries (left/right walls)
        mask = self.particles_positions[:, 0] < 0
        self.particles_positions[mask, 0] = 0
        self.particles_velocities[mask, 0] *= -0.5
        
        mask = self.particles_positions[:, 0] > ROOM_WIDTH
        self.particles_positions[mask, 0] = ROOM_WIDTH
        self.particles_velocities[mask, 0] *= -0.5
        
        # Y boundaries (floor/ceiling)
        mask = self.particles_positions[:, 1] < 0
        self.particles_positions[mask, 1] = 0
        self.particles_velocities[mask, 1] *= -0.5
        
        mask = self.particles_positions[:, 1] > ROOM_HEIGHT
        self.particles_positions[mask, 1] = ROOM_HEIGHT
        self.particles_velocities[mask, 1] *= -0.5
        
        # Z boundaries (front/back walls)
        mask = self.particles_positions[:, 2] < 0
        self.particles_positions[mask, 2] = 0
        self.particles_velocities[mask, 2] *= -0.5
        
        # Back wall with fan - particles near fan are removed
        mask = self.particles_positions[:, 2] > ROOM_LENGTH - 0.5
        near_fan = mask.copy()
        
        # Check if near fan position
        if np.any(near_fan):
            distances_to_fan = np.linalg.norm(
                self.particles_positions[near_fan] - self.fan.position,
                axis=1
            )
            # Remove particles very close to fan (exhausted)
            remove_mask = near_fan.copy()
            remove_mask[near_fan] = distances_to_fan < self.fan.radius * 2
            self._remove_particles(remove_mask)
        else:
            # Regular wall bounce
            self.particles_positions[mask, 2] = ROOM_LENGTH
            self.particles_velocities[mask, 2] *= -0.5
    
    def remove_old_particles(self):
        """Remove particles that are too old or exhausted."""
        # Remove old particles
        old_mask = self.particles_ages > 300.0  # 5 minutes
        self._remove_particles(old_mask)
    
    def _remove_particles(self, mask):
        """Remove particles indicated by boolean mask.
        
        Args:
            mask: Boolean array indicating which particles to remove
        """
        num_removed = np.sum(mask)
        if num_removed > 0:
            keep_mask = ~mask
            self.particles_positions = self.particles_positions[keep_mask]
            self.particles_velocities = self.particles_velocities[keep_mask]
            self.particles_ages = self.particles_ages[keep_mask]
            self.particles_removed += num_removed
    
    def update(self, dt):
        """Update simulation for one time step.
        
        Args:
            dt: Time step in seconds
        """
        # Update cigar states (puffing, burn time, etc.)
        self.cigar_manager.update(dt)
        
        # Generate new particles
        self.generate_particles(dt)
        
        # Apply physics
        self.apply_physics(dt)
        
        # Remove old particles
        self.remove_old_particles()
        
        # Update time
        self.time += dt
        
        # Print height distribution periodically for debugging
        if self.time - self.last_height_print_time >= self.height_print_interval:
            self.print_height_distribution()
            self.last_height_print_time = self.time
    
    def get_particle_count(self):
        """Get current number of particles.
        
        Returns:
            Number of active particles
        """
        return len(self.particles_positions)
    
    def get_particles(self):
        """Get particle positions for rendering/analysis.
        
        Returns:
            numpy array of particle positions
        """
        return self.particles_positions.copy()
    
    def calculate_room_average_ppm(self):
        """Calculate average PPM across the entire room.
        
        Returns:
            Average PPM value
        """
        if len(self.particles_positions) == 0:
            return 0.0
        
        # Simple model: particles per cubic foot
        particles_per_cubic_foot = len(self.particles_positions) / self.room.volume
        avg_ppm = particles_per_cubic_foot * 10  # Scaling factor
        return avg_ppm
    
    def calculate_room_average_clarity(self):
        """Calculate average clarity across the room.
        
        Returns:
            Average clarity percentage
        """
        avg_ppm = self.calculate_room_average_ppm()
        path_length = 10.0  # Assume 10 feet visibility
        clarity = 100.0 * np.exp(-0.0001 * avg_ppm * path_length)
        return np.clip(clarity, 0.0, 100.0)
    
    def reset(self):
        """Reset simulation to initial state."""
        self.particles_positions = np.zeros((0, 3), dtype=float)
        self.particles_velocities = np.zeros((0, 3), dtype=float)
        self.particles_ages = np.zeros(0, dtype=float)
        self.time = 0.0
        self.particles_generated = 0
        self.particles_removed = 0
        self.particle_accumulator = 0.0
        self.last_height_print_time = 0.0
        self.cigar_manager.reset()
    
    def get_height_distribution(self):
        """Calculate particle distribution across height zones.
        
        Returns:
            Dictionary with particle counts in each height zone
        """
        if len(self.particles_positions) == 0:
            return {
                'zone_0_4': 0,
                'zone_4_8': 0,
                'zone_8_14': 0,
                'zone_14_18': 0,
                'zone_18_plus': 0,
                'total': 0
            }
        
        heights = self.particles_positions[:, 1]
        
        zone_0_4 = np.sum(heights < 4.0)
        zone_4_8 = np.sum((heights >= 4.0) & (heights < 8.0))
        zone_8_14 = np.sum((heights >= 8.0) & (heights < 14.0))
        zone_14_18 = np.sum((heights >= 14.0) & (heights < 18.0))
        zone_18_plus = np.sum(heights >= 18.0)
        
        return {
            'zone_0_4': int(zone_0_4),
            'zone_4_8': int(zone_4_8),
            'zone_8_14': int(zone_8_14),
            'zone_14_18': int(zone_14_18),
            'zone_18_plus': int(zone_18_plus),
            'total': len(self.particles_positions)
        }
    
    def print_height_distribution(self):
        """Print particle height distribution to console for debugging."""
        dist = self.get_height_distribution()
        
        if dist['total'] == 0:
            return
        
        # Calculate percentages
        pct_0_4 = (dist['zone_0_4'] / dist['total']) * 100
        pct_4_8 = (dist['zone_4_8'] / dist['total']) * 100
        pct_8_14 = (dist['zone_8_14'] / dist['total']) * 100
        pct_14_18 = (dist['zone_14_18'] / dist['total']) * 100
        pct_18_plus = (dist['zone_18_plus'] / dist['total']) * 100
        
        print(f"\n📊 SMOKE HEIGHT DISTRIBUTION @ t={self.time:.1f}s")
        print(f"   Total particles: {dist['total']}")
        print(f"   0-4 ft (rise zone):     {dist['zone_0_4']:6d} ({pct_0_4:5.1f}%)")
        print(f"   4-8 ft (HOVER ZONE):    {dist['zone_4_8']:6d} ({pct_4_8:5.1f}%) ⭐")
        print(f"   8-14 ft (slow rise):    {dist['zone_8_14']:6d} ({pct_8_14:5.1f}%)")
        print(f"   14-18 ft (upper zone):  {dist['zone_14_18']:6d} ({pct_14_18:5.1f}%)")
        print(f"   18+ ft (near ceiling):  {dist['zone_18_plus']:6d} ({pct_18_plus:5.1f}%)")
    
    def get_statistics(self):
        """Get simulation statistics.
        
        Returns:
            Dictionary with simulation statistics
        """
        stats = {
            'time': self.time,
            'particle_count': self.get_particle_count(),
            'particles_generated': self.particles_generated,
            'particles_removed': self.particles_removed,
            'num_smokers': self.num_smokers,
            'avg_ppm': self.calculate_room_average_ppm(),
            'avg_clarity': self.calculate_room_average_clarity()
        }
        
        # Add height distribution to statistics
        stats.update(self.get_height_distribution())
        
        return stats
