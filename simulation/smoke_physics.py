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
                
                # Add small random offset to positions
                cigar_positions += np.random.normal(0, 0.2, size=(num_particles, 3))
                
                # Initial velocity (slightly upward due to heat)
                cigar_velocities = np.random.normal(0, 0.5, size=(num_particles, 3))
                cigar_velocities[:, 1] += 1.0  # Upward bias
                
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
    
    def apply_physics(self, dt):
        """Apply physics forces to all particles.
        
        Args:
            dt: Time step in seconds
        """
        if len(self.particles_positions) == 0:
            return
        
        # 1. Buoyancy (upward force due to temperature difference)
        # Smoke rises SLOWLY due to being warmer than ambient air
        buoyancy = np.zeros_like(self.particles_velocities)
        buoyancy[:, 1] = BUOYANCY_FACTOR * GRAVITY
        
        # Reduce buoyancy for older particles (as they cool and equilibrate)
        # But never apply downward force - smoke doesn't fall
        age_factor = np.clip(1.0 - (self.particles_ages / 600.0), 0.3, 1.0)  # Keep 30% buoyancy even when old
        buoyancy[:, 1] *= age_factor.reshape(-1)
        
        # 2. Diffusion (random walk for spreading)
        # Stronger horizontal diffusion to model air currents and mixing
        diffusion = np.random.normal(0, DIFFUSION_COEFFICIENT, size=self.particles_velocities.shape)
        # Reduce vertical diffusion to keep smoke more stable at its level
        diffusion[:, 1] *= 0.3
        
        # 3. Fan suction (advection toward fan)
        fan_velocities = self.fan.calculate_velocity_field(self.particles_positions)
        
        # NOTE: No gravity applied to smoke particles
        # Smoke does NOT fall - it lingers and gradually rises
        
        # Combine forces
        acceleration = buoyancy + diffusion + fan_velocities
        
        # Update velocities
        self.particles_velocities += acceleration * dt
        
        # Apply stronger damping for realistic slow motion
        # This makes smoke linger at its current level while drifting slowly
        damping = 0.90  # Increased damping (was 0.95) for more stable behavior
        self.particles_velocities *= damping
        
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
        self.cigar_manager.reset()
    
    def get_statistics(self):
        """Get simulation statistics.
        
        Returns:
            Dictionary with simulation statistics
        """
        return {
            'time': self.time,
            'particle_count': self.get_particle_count(),
            'particles_generated': self.particles_generated,
            'particles_removed': self.particles_removed,
            'num_smokers': self.num_smokers,
            'avg_ppm': self.calculate_room_average_ppm(),
            'avg_clarity': self.calculate_room_average_clarity()
        }
