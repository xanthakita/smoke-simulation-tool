"""3D visualization renderer using matplotlib."""

import numpy as np
import matplotlib
matplotlib.use('Qt5Agg')

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D
from PyQt5.QtWidgets import QWidget, QVBoxLayout

from utils.constants import (
    ROOM_WIDTH, ROOM_LENGTH, ROOM_HEIGHT,
    COLOR_SMOKE, COLOR_SENSOR_LOW, COLOR_SENSOR_HIGH, COLOR_FAN
)


class Renderer3D(QWidget):
    """3D visualization widget for smoke simulation."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Create matplotlib figure and canvas
        self.figure = Figure(figsize=(10, 8))
        self.canvas = FigureCanvas(self.figure)
        
        # Create 3D axis
        self.ax = self.figure.add_subplot(111, projection='3d')
        
        # Set background color
        self.figure.patch.set_facecolor('#2c3e50')
        self.ax.set_facecolor('#34495e')
        
        # Initialize simulation references
        self.smoke_sim = None
        self.fan = None
        self.sensor_pairs = []
        
        # Setup layout
        layout = QVBoxLayout(self)
        layout.addWidget(self.canvas)
        
        # Initial setup
        self.setup_axes()
        
    def set_simulation_refs(self, smoke_sim, fan, sensor_pairs):
        """Set references to simulation objects.
        
        Args:
            smoke_sim: SmokeSimulation object
            fan: ExhaustFan object
            sensor_pairs: List of SensorPair objects
        """
        self.smoke_sim = smoke_sim
        self.fan = fan
        self.sensor_pairs = sensor_pairs
        self.update()
        
    def setup_axes(self):
        """Setup 3D axes with room boundaries."""
        # Clear previous plot
        self.ax.clear()
        
        # Set labels and title
        self.ax.set_xlabel('Width (ft)', color='white')
        self.ax.set_ylabel('Length (ft)', color='white')
        self.ax.set_zlabel('Height (ft)', color='white')
        
        # Set axis limits
        self.ax.set_xlim(0, ROOM_WIDTH)
        self.ax.set_ylim(0, ROOM_LENGTH)
        self.ax.set_zlim(0, ROOM_HEIGHT)
        
        # Set tick colors
        self.ax.tick_params(axis='x', colors='white')
        self.ax.tick_params(axis='y', colors='white')
        self.ax.tick_params(axis='z', colors='white')
        
        # Draw room wireframe
        self.draw_room_wireframe()
        
    def draw_room_wireframe(self):
        """Draw wireframe representation of the room."""
        # Define room corners
        corners = np.array([
            [0, 0, 0],
            [ROOM_WIDTH, 0, 0],
            [ROOM_WIDTH, ROOM_LENGTH, 0],
            [0, ROOM_LENGTH, 0],
            [0, 0, ROOM_HEIGHT],
            [ROOM_WIDTH, 0, ROOM_HEIGHT],
            [ROOM_WIDTH, ROOM_LENGTH, ROOM_HEIGHT],
            [0, ROOM_LENGTH, ROOM_HEIGHT]
        ])
        
        # Define edges connecting corners
        edges = [
            (0, 1), (1, 2), (2, 3), (3, 0),  # Bottom face
            (4, 5), (5, 6), (6, 7), (7, 4),  # Top face
            (0, 4), (1, 5), (2, 6), (3, 7)   # Vertical edges
        ]
        
        # Draw edges
        for edge in edges:
            points = corners[list(edge)]
            self.ax.plot3D(*points.T, color='gray', alpha=0.3, linewidth=1)
        
    def draw_fan(self):
        """Draw fan marker."""
        if self.fan is None:
            return
        
        pos = self.fan.position
        
        # Draw fan as a sphere
        u = np.linspace(0, 2 * np.pi, 20)
        v = np.linspace(0, np.pi, 20)
        radius = self.fan.radius
        
        x = pos[0] + radius * np.outer(np.cos(u), np.sin(v))
        y = pos[2] + radius * np.outer(np.sin(u), np.sin(v))  # Note: using z for y-axis (length)
        z = pos[1] + radius * np.outer(np.ones(np.size(u)), np.cos(v))  # Note: using y for z-axis (height)
        
        self.ax.plot_surface(x, y, z, color=COLOR_FAN, alpha=0.6)
        
        # Draw fan label
        self.ax.text(pos[0], pos[2], pos[1] + 1, 'FAN', color='white', fontsize=10, weight='bold')
        
    def draw_sensors(self):
        """Draw sensor markers."""
        if not self.sensor_pairs:
            return
        
        for pair in self.sensor_pairs:
            # Low sensor (green)
            low_pos = pair.low_sensor.position
            self.ax.scatter(
                [low_pos[0]], [low_pos[2]], [low_pos[1]],  # Note coordinate remapping
                color=COLOR_SENSOR_LOW,
                s=100,
                marker='o',
                edgecolors='white',
                linewidths=2,
                alpha=0.8
            )
            
            # High sensor (red)
            high_pos = pair.high_sensor.position
            self.ax.scatter(
                [high_pos[0]], [high_pos[2]], [high_pos[1]],  # Note coordinate remapping
                color=COLOR_SENSOR_HIGH,
                s=100,
                marker='o',
                edgecolors='white',
                linewidths=2,
                alpha=0.8
            )
            
            # Draw line connecting sensor pair
            self.ax.plot3D(
                [low_pos[0], high_pos[0]],
                [low_pos[2], high_pos[2]],
                [low_pos[1], high_pos[1]],
                color='white',
                alpha=0.5,
                linewidth=1,
                linestyle='--'
            )
            
            # Add labels with trip status
            if pair.is_tripped:
                label = f'P{pair.pair_id} TRIP'
                color = 'red'
            else:
                label = f'P{pair.pair_id}'
                color = 'white'
            
            # Label at midpoint
            mid_x = (low_pos[0] + high_pos[0]) / 2
            mid_y = (low_pos[2] + high_pos[2]) / 2
            mid_z = (low_pos[1] + high_pos[1]) / 2
            
            self.ax.text(mid_x, mid_y, mid_z, label, color=color, fontsize=8, weight='bold')
        
    def draw_particles(self):
        """Draw smoke particles."""
        if self.smoke_sim is None:
            return
        
        particles = self.smoke_sim.get_particles()
        
        if len(particles) == 0:
            return
        
        # Sample particles for visualization (too many particles slow down rendering)
        max_display_particles = 2000
        if len(particles) > max_display_particles:
            indices = np.random.choice(len(particles), max_display_particles, replace=False)
            particles = particles[indices]
        
        # Extract coordinates (note coordinate remapping for display)
        # Data is stored as [x, y, z] where x=width, y=height, z=length
        # Display as x=width, y=length, z=height
        x = particles[:, 0]  # Width
        y = particles[:, 2]  # Length (from data z)
        z = particles[:, 1]  # Height (from data y)
        
        # Draw particles as scatter plot
        self.ax.scatter(
            x, y, z,
            c=COLOR_SMOKE,
            s=5,
            alpha=0.2,
            edgecolors='none'
        )
        
    def update(self):
        """Update the visualization."""
        # Setup axes (clears previous plot)
        self.setup_axes()
        
        # Draw components
        self.draw_fan()
        self.draw_sensors()
        self.draw_particles()
        
        # Set viewing angle for better perspective
        self.ax.view_init(elev=20, azim=45)
        
        # Refresh canvas
        self.canvas.draw()
