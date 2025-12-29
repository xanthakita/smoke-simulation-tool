"""Room model and properties."""

import numpy as np
from utils.constants import ROOM_WIDTH, ROOM_LENGTH, ROOM_HEIGHT, ROOM_VOLUME


class Room:
    """Represents the cigar lounge room."""
    
    def __init__(self):
        """Initialize the room with dimensions and properties."""
        self.width = ROOM_WIDTH
        self.length = ROOM_LENGTH
        self.height = ROOM_HEIGHT
        self.volume = ROOM_VOLUME
        
        # Room boundaries
        self.x_min, self.x_max = 0.0, ROOM_WIDTH
        self.y_min, self.y_max = 0.0, ROOM_HEIGHT
        self.z_min, self.z_max = 0.0, ROOM_LENGTH
        
        # Smoker positions (distributed throughout the room)
        self.smoker_positions = []
        
    def generate_smoker_positions(self, num_smokers, smoker_height):
        """Generate random positions for smokers throughout the room.
        
        Args:
            num_smokers: Number of smokers in the room
            smoker_height: Height of cigar when sitting (feet)
            
        Returns:
            numpy array of shape (num_smokers, 3) with positions
        """
        # Distribute smokers in a grid-like pattern with some randomization
        # Leave space near walls and fan
        margin_x = 3.0  # feet from North/South walls (x-axis)
        margin_z = 5.0  # feet from East/West walls (z-axis)
        
        positions = []
        
        # Calculate grid dimensions
        grid_cols = int(np.sqrt(num_smokers * self.width / self.length))
        grid_rows = int(np.ceil(num_smokers / grid_cols))
        
        spacing_x = (self.width - 2 * margin_x) / (grid_cols + 1)
        spacing_z = (self.length - 2 * margin_z) / (grid_rows + 1)
        
        smoker_idx = 0
        for row in range(grid_rows):
            for col in range(grid_cols):
                if smoker_idx >= num_smokers:
                    break
                    
                # Base position with some randomization
                x = margin_x + (col + 1) * spacing_x + np.random.uniform(-spacing_x/3, spacing_x/3)
                z = margin_z + (row + 1) * spacing_z + np.random.uniform(-spacing_z/3, spacing_z/3)
                y = smoker_height
                
                # Ensure within bounds
                x = np.clip(x, margin_x, self.width - margin_x)
                z = np.clip(z, margin_z, self.length - margin_z)
                
                positions.append([x, y, z])
                smoker_idx += 1
                
            if smoker_idx >= num_smokers:
                break
        
        self.smoker_positions = np.array(positions)
        return self.smoker_positions
    
    def is_inside(self, position):
        """Check if a position is inside the room.
        
        Args:
            position: numpy array [x, y, z]
            
        Returns:
            Boolean indicating if position is inside room
        """
        x, y, z = position
        return (self.x_min <= x <= self.x_max and
                self.y_min <= y <= self.y_max and
                self.z_min <= z <= self.z_max)
    
    def constrain_to_bounds(self, positions):
        """Constrain positions to room boundaries.
        
        Args:
            positions: numpy array of shape (N, 3)
            
        Returns:
            Constrained positions
        """
        positions[:, 0] = np.clip(positions[:, 0], self.x_min, self.x_max)
        positions[:, 1] = np.clip(positions[:, 1], self.y_min, self.y_max)
        positions[:, 2] = np.clip(positions[:, 2], self.z_min, self.z_max)
        return positions
    
    def get_bounds(self):
        """Get room boundaries.
        
        Returns:
            Tuple of (x_min, x_max, y_min, y_max, z_min, z_max)
        """
        return (self.x_min, self.x_max, self.y_min, self.y_max, self.z_min, self.z_max)
    
    def get_dimensions(self):
        """Get room dimensions.
        
        Returns:
            Tuple of (width, length, height)
        """
        return (self.width, self.length, self.height)
