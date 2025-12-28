"""Cigar smoking behavior model."""

import numpy as np
from datetime import datetime


class Cigar:
    """Represents an individual cigar being smoked."""
    
    def __init__(self, position, cigar_id=0, stagger_start=True):
        """Initialize a cigar.
        
        Args:
            position: numpy array [x, y, z] position of the smoker
            cigar_id: Unique identifier for this cigar
            stagger_start: If True, start with random age between 0-50 minutes
        """
        self.id = cigar_id
        self.position = np.array(position, dtype=float)
        self.burn_time = 50.0 * 60.0  # 50 minutes in seconds
        
        # Stagger initial ages to simulate cigars at different burn stages
        if stagger_start:
            self.age = np.random.uniform(0.0, self.burn_time)  # Random age 0-50 minutes
            age_minutes = int(self.age / 60)
            print(f"[INIT] Cigar #{cigar_id} starting at age {age_minutes} minutes (staggered start)")
        else:
            self.age = 0.0  # Time since lit (seconds)
            print(f"[INIT] Cigar #{cigar_id} starting fresh at age 0 minutes")
        
        self.is_active = True
        
        # Puff timing
        self.time_since_last_puff = np.random.uniform(0.0, 30.0)  # Random start in puff cycle
        self.next_puff_interval = self._generate_puff_interval()
        self.is_puffing = False
        self.puff_duration = 4.0  # Puff lasts 4 seconds (longer for visibility)
        self.puff_timer = 0.0
        
        # Smoke generation rates
        self.baseline_rate = 100  # Particles per second between puffs
        self.puff_rate = 6000  # Particles per second during puff (30x baseline for dramatic effect!)
        
    def _generate_puff_interval(self):
        """Generate random interval until next puff (0.5 to 3 minutes).
        
        Returns:
            Time in seconds until next puff
        """
        return np.random.uniform(30.0, 180.0)  # 0.5 to 3 minutes in seconds
    
    def update(self, dt):
        """Update cigar state.
        
        Args:
            dt: Time step in seconds
        """
        if not self.is_active:
            return
        
        # Update age
        self.age += dt
        
        # Check if cigar is finished
        if self.age >= self.burn_time:
            self.is_active = False
            return
        
        # Update puff state
        if self.is_puffing:
            self.puff_timer += dt
            if self.puff_timer >= self.puff_duration:
                # Puff finished
                self.is_puffing = False
                self.puff_timer = 0.0
                self.next_puff_interval = self._generate_puff_interval()
                self.time_since_last_puff = 0.0
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Cigar #{self.id} - Puff ended")
        else:
            self.time_since_last_puff += dt
            if self.time_since_last_puff >= self.next_puff_interval:
                # Start new puff
                self.is_puffing = True
                self.puff_timer = 0.0
                # Log puff event to console for debugging
                age_minutes = int(self.age / 60)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 💨 PUFF EVENT! Cigar #{self.id} at position {self.position} (age: {age_minutes} min)")
    
    def get_smoke_generation_rate(self):
        """Get current smoke generation rate based on cigar state.
        
        Returns:
            Particles per second to generate
        """
        if not self.is_active:
            return 0.0
        
        # Calculate burn progress (0.0 to 1.0)
        burn_progress = self.age / self.burn_time
        
        # Diminishing rate over lifetime (more smoke at start, less at end)
        # Use exponential decay
        lifetime_factor = np.exp(-2.0 * burn_progress)  # Decays to ~0.14 at end
        lifetime_factor = max(0.3, lifetime_factor)  # Don't go below 30% of initial rate
        
        if self.is_puffing:
            # Large burst of smoke during puff
            return self.puff_rate * lifetime_factor
        else:
            # Low baseline smoke between puffs
            return self.baseline_rate * lifetime_factor
    
    def get_position(self):
        """Get cigar position.
        
        Returns:
            numpy array [x, y, z]
        """
        return self.position.copy()
    
    def relight(self):
        """Relight the cigar (start a new one at same position)."""
        self.age = 0.0
        self.is_active = True
        self.time_since_last_puff = 0.0
        self.next_puff_interval = self._generate_puff_interval()
        self.is_puffing = False
        self.puff_timer = 0.0


class CigarManager:
    """Manages all active cigars in the simulation."""
    
    def __init__(self, room):
        """Initialize cigar manager.
        
        Args:
            room: Room object
        """
        self.room = room
        self.cigars = []
        self.num_smokers = 0
        self.smoker_positions = np.zeros((0, 3), dtype=float)
        self.next_cigar_id = 0
    
    def set_num_smokers(self, num_smokers, smoker_positions):
        """Set number of active smokers and create cigars.
        
        Args:
            num_smokers: Number of smokers
            smoker_positions: numpy array of smoker positions
        """
        self.num_smokers = num_smokers
        self.smoker_positions = smoker_positions.copy()
        
        # Create cigars for each smoker
        self.cigars = []
        for i in range(num_smokers):
            position = self.smoker_positions[i]
            cigar = Cigar(position, cigar_id=self.next_cigar_id)
            self.cigars.append(cigar)
            self.next_cigar_id += 1
    
    def update(self, dt):
        """Update all cigars.
        
        Args:
            dt: Time step in seconds
        """
        for cigar in self.cigars:
            cigar.update(dt)
            
            # If cigar is finished, relight it (start a new one)
            if not cigar.is_active:
                cigar.relight()
    
    def get_total_smoke_rate(self):
        """Get total smoke generation rate from all cigars.
        
        Returns:
            Total particles per second
        """
        total_rate = sum(cigar.get_smoke_generation_rate() for cigar in self.cigars)
        return total_rate
    
    def get_smoke_sources(self):
        """Get list of active smoke source positions and their rates.
        
        Returns:
            List of tuples (position, rate)
        """
        sources = []
        for cigar in self.cigars:
            if cigar.is_active:
                sources.append((cigar.get_position(), cigar.get_smoke_generation_rate()))
        return sources
    
    def reset(self):
        """Reset all cigars."""
        self.cigars = []
        self.next_cigar_id = 0
