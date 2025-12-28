"""3D visualization renderer using matplotlib."""

import numpy as np
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import QTimer
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Line3DCollection

from utils.constants import (
    COLOR_SMOKE, COLOR_SENSOR_LOW, COLOR_SENSOR_HIGH, COLOR_FAN, COLOR_ROOM,
    PARTICLE_RENDER_SIZE, PARTICLE_ALPHA, ROOM_WIDTH, ROOM_LENGTH, ROOM_HEIGHT
)


class Renderer3D(QWidget):
    """3D matplotlib renderer for smoke simulation."""
    
    def __init__(self, parent=None):
        """Initialize 3D renderer.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Create matplotlib figure and canvas
        self.fig = Figure(figsize=(10, 8), facecolor='#1a1a26')
        self.canvas = FigureCanvas(self.fig)
        self.ax = self.fig.add_subplot(111, projection='3d', facecolor='#1a1a26')
        
        # Setup layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)
        
        # Camera settings (matplotlib uses view angle instead)
        # Elevation: angle above horizontal (20 = looking slightly down)
        # Azimuth: rotation around vertical axis (-60 = viewing from front-left corner)
        self.camera_elevation = 20.0  # degrees (look slightly down from above)
        self.camera_azimuth = -60.0   # degrees (view from front-left corner)
        self.camera_distance = 100.0
        
        # Simulation references (set externally)
        self.smoke_sim = None
        self.fan = None
        self.sensor_pairs = []
        
        # Rendering options
        self.show_particles = True
        self.show_sensors = True
        self.show_fan = True
        self.show_room = True
        
        # Cache for plot artists
        self._room_lines = None
        self._fan_artists = []
        self._sensor_artists = []
        self._particle_scatter = None
        
        # Initialize the 3D view
        self._setup_axes()
        
    def _setup_axes(self):
        """Setup 3D axes with appropriate limits and styling.
        
        Coordinate system:
        - X-axis: Width (0-30 ft) - horizontal left/right
        - Y-axis: Height (0-20 ft) - vertical up/down
        - Z-axis: Length (0-75 ft) - horizontal front/back (depth)
        """
        # Set axis limits with correct room dimensions
        self.ax.set_xlim(0, ROOM_WIDTH)   # 0-30 ft (Width)
        self.ax.set_ylim(0, ROOM_HEIGHT)  # 0-20 ft (Height - VERTICAL)
        self.ax.set_zlim(0, ROOM_LENGTH)  # 0-75 ft (Length/Depth)
        
        # Set labels with clear dimension indicators
        self.ax.set_xlabel('Width (ft)', color='white', fontsize=10, labelpad=8)
        self.ax.set_ylabel('Height (ft)', color='white', fontsize=10, labelpad=8)
        self.ax.set_zlabel('Length (ft)', color='white', fontsize=10, labelpad=8)
        
        # Set title with room dimensions
        title = f'3D Smoke Simulation View\nRoom: {ROOM_WIDTH:.0f}ft (W) × {ROOM_HEIGHT:.0f}ft (H) × {ROOM_LENGTH:.0f}ft (L)'
        self.ax.set_title(title, color='white', fontsize=11, pad=15)
        
        # Customize grid and pane colors
        self.ax.xaxis.pane.fill = False
        self.ax.yaxis.pane.fill = False
        self.ax.zaxis.pane.fill = False
        self.ax.xaxis.pane.set_edgecolor('#2a2a35')
        self.ax.yaxis.pane.set_edgecolor('#2a2a35')
        self.ax.zaxis.pane.set_edgecolor('#2a2a35')
        
        # Grid styling
        self.ax.grid(True, alpha=0.3, color='#4a4a55')
        
        # Tick label colors
        self.ax.tick_params(colors='white', labelsize=8)
        
        # Set initial view angle to show room upright
        # elevation=20: look down from slightly above
        # azimuth=-60: view from front-left corner (shows width, height, and depth)
        self.ax.view_init(elev=self.camera_elevation, azim=self.camera_azimuth)
        
        # Force equal aspect ratio to prevent distortion
        # This helps maintain proper room proportions
        try:
            self.ax.set_box_aspect([ROOM_WIDTH, ROOM_HEIGHT, ROOM_LENGTH])
        except:
            # Fallback for older matplotlib versions
            pass
        
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
        
    def update(self):
        """Update the 3D visualization."""
        # Clear previous artists (except axes setup)
        if self._particle_scatter:
            self._particle_scatter.remove()
            self._particle_scatter = None
        
        for artist in self._fan_artists:
            artist.remove()
        self._fan_artists.clear()
        
        for artist in self._sensor_artists:
            artist.remove()
        self._sensor_artists.clear()
        
        # Draw scene components
        if self.show_room and self._room_lines is None:
            self._draw_room()
        
        if self.show_fan and self.fan:
            self._draw_fan()
        
        if self.show_sensors:
            self._draw_sensors()
        
        if self.show_particles and self.smoke_sim:
            self._draw_particles()
        
        # Refresh canvas
        self.canvas.draw_idle()
        
    def _draw_room(self):
        """Draw room boundaries with correct coordinate mapping.
        
        Coordinate system:
        - X: Width (0-30 ft) - left/right
        - Y: Height (0-20 ft) - floor/ceiling (VERTICAL)
        - Z: Length (0-75 ft) - front/back (depth)
        
        Room corners:
        - Front-left-bottom: (0, 0, 0)
        - Front-right-bottom: (30, 0, 0)
        - Back-right-bottom: (30, 0, 75)
        - Back-left-bottom: (0, 0, 75)
        - Front-left-top: (0, 20, 0)
        - Front-right-top: (30, 20, 0)
        - Back-right-top: (30, 20, 75)
        - Back-left-top: (0, 20, 75)
        """
        if self._room_lines is not None:
            return  # Already drawn
        
        # Define room edges (bottom and top rectangles + vertical edges)
        # Format: [[x1, y1, z1], [x2, y2, z2]]
        edges = [
            # FLOOR (Y=0) - Bottom rectangle
            [[0, 0, 0], [ROOM_WIDTH, 0, 0]],              # Front edge (width)
            [[ROOM_WIDTH, 0, 0], [ROOM_WIDTH, 0, ROOM_LENGTH]],  # Right edge (length)
            [[ROOM_WIDTH, 0, ROOM_LENGTH], [0, 0, ROOM_LENGTH]], # Back edge (width)
            [[0, 0, ROOM_LENGTH], [0, 0, 0]],             # Left edge (length)
            
            # CEILING (Y=ROOM_HEIGHT) - Top rectangle  
            [[0, ROOM_HEIGHT, 0], [ROOM_WIDTH, ROOM_HEIGHT, 0]],  # Front edge
            [[ROOM_WIDTH, ROOM_HEIGHT, 0], [ROOM_WIDTH, ROOM_HEIGHT, ROOM_LENGTH]],  # Right edge
            [[ROOM_WIDTH, ROOM_HEIGHT, ROOM_LENGTH], [0, ROOM_HEIGHT, ROOM_LENGTH]], # Back edge
            [[0, ROOM_HEIGHT, ROOM_LENGTH], [0, ROOM_HEIGHT, 0]],  # Left edge
            
            # VERTICAL EDGES (connecting floor to ceiling)
            [[0, 0, 0], [0, ROOM_HEIGHT, 0]],                     # Front-left corner
            [[ROOM_WIDTH, 0, 0], [ROOM_WIDTH, ROOM_HEIGHT, 0]],   # Front-right corner
            [[ROOM_WIDTH, 0, ROOM_LENGTH], [ROOM_WIDTH, ROOM_HEIGHT, ROOM_LENGTH]],  # Back-right corner
            [[0, 0, ROOM_LENGTH], [0, ROOM_HEIGHT, ROOM_LENGTH]], # Back-left corner
        ]
        
        # Draw room edges
        for edge in edges:
            xs = [edge[0][0], edge[1][0]]
            ys = [edge[0][1], edge[1][1]]
            zs = [edge[0][2], edge[1][2]]
            line = self.ax.plot(xs, ys, zs, color=COLOR_ROOM, linewidth=2, alpha=0.7)[0]
            if self._room_lines is None:
                self._room_lines = [line]
            else:
                self._room_lines.append(line)
        
        # Draw floor grid (on Y=0 plane)
        # Grid lines parallel to length (Z-axis) at regular X intervals
        grid_spacing = 5
        for i in range(0, int(ROOM_WIDTH) + 1, grid_spacing):
            xs = [i, i]           # X position (constant across line)
            ys = [0, 0]           # Floor level (Y=0)
            zs = [0, ROOM_LENGTH] # Full length (Z from 0 to 75)
            line = self.ax.plot(xs, ys, zs, color='#4a4a55', linewidth=0.5, alpha=0.3)[0]
            self._room_lines.append(line)
        
        # Grid lines parallel to width (X-axis) at regular Z intervals    
        for i in range(0, int(ROOM_LENGTH) + 1, grid_spacing):
            xs = [0, ROOM_WIDTH]  # Full width (X from 0 to 30)
            ys = [0, 0]           # Floor level (Y=0)
            zs = [i, i]           # Z position (constant across line)
            line = self.ax.plot(xs, ys, zs, color='#4a4a55', linewidth=0.5, alpha=0.3)[0]
            self._room_lines.append(line)
    
    def _draw_fan(self):
        """Draw exhaust fan on back wall.
        
        Fan position: [5.0, 15.0, 75.0]
        - X = 5 ft from left wall
        - Y = 15 ft up from floor
        - Z = 75 ft (on back wall)
        
        Fan circle is drawn in XY plane at Z=75 (perpendicular to back wall)
        """
        if not self.fan:
            return
        
        pos = self.fan.position  # [X, Y, Z] = [5, 15, 75]
        radius = self.fan.radius
        
        # Fan color based on speed (brighter when running faster)
        intensity = self.fan.speed_percent / 100.0
        color = (
            COLOR_FAN[0] * (0.3 + 0.7 * intensity),
            COLOR_FAN[1] * (0.3 + 0.7 * intensity),
            COLOR_FAN[2] * (0.3 + 0.7 * intensity)
        )
        
        # Draw fan circle (in XY plane at Z=75, since fan is on back wall)
        segments = 24
        angles = np.linspace(0, 2 * np.pi, segments + 1)
        
        # Fan circle coordinates - circle in XY plane, constant Z
        circle_x = pos[0] + radius * np.cos(angles)  # X varies around center
        circle_y = pos[1] + radius * np.sin(angles)  # Y varies around center
        circle_z = np.full(segments + 1, pos[2])      # Z constant at back wall (75)
        
        line = self.ax.plot(circle_x, circle_y, circle_z, color=color, linewidth=2.5)[0]
        self._fan_artists.append(line)
        
        # Draw fan blades (4 spokes) - also in XY plane
        for i in range(4):
            angle = 2.0 * np.pi * i / 4
            end_x = pos[0] + radius * np.cos(angle)
            end_y = pos[1] + radius * np.sin(angle)
            line = self.ax.plot(
                [pos[0], end_x],    # X from center to edge
                [pos[1], end_y],    # Y from center to edge
                [pos[2], pos[2]],   # Z constant at back wall
                color=color, linewidth=2.5
            )[0]
            self._fan_artists.append(line)
        
        # Draw center point
        scatter = self.ax.scatter([pos[0]], [pos[1]], [pos[2]], 
                                 color=color, s=50, marker='o', edgecolors='white', linewidths=1)
        self._fan_artists.append(scatter)
    
    def _draw_sensors(self):
        """Draw sensor positions.
        
        Sensors are positioned in pairs (low/high) at various locations in the room.
        Each sensor position is [X, Y, Z]:
        - X: varies based on fan position and pair ID (spread across width)
        - Y: low_height (e.g., 5 ft) or high_height (e.g., 15 ft)
        - Z: varies based on distance from fan (toward front of room)
        """
        for pair in self.sensor_pairs:
            # Draw low sensor (green square) - lower height
            low_pos = pair.low_sensor.position  # [X, Y_low, Z]
            scatter = self.ax.scatter(
                [low_pos[0]], [low_pos[1]], [low_pos[2]],
                color=COLOR_SENSOR_LOW, s=120, marker='s',
                edgecolors='white', linewidths=1.5, alpha=0.9
            )
            self._sensor_artists.append(scatter)
            
            # Draw high sensor (red square) - higher height
            high_pos = pair.high_sensor.position  # [X, Y_high, Z]
            scatter = self.ax.scatter(
                [high_pos[0]], [high_pos[1]], [high_pos[2]],
                color=COLOR_SENSOR_HIGH, s=120, marker='s',
                edgecolors='white', linewidths=1.5, alpha=0.9
            )
            self._sensor_artists.append(scatter)
            
            # Draw line connecting pair (same X,Z but different Y)
            line = self.ax.plot(
                [low_pos[0], high_pos[0]],  # X coordinates
                [low_pos[1], high_pos[1]],  # Y coordinates (vertical line)
                [low_pos[2], high_pos[2]],  # Z coordinates
                color='white', linewidth=1.5, alpha=0.4, linestyle='--'
            )[0]
            self._sensor_artists.append(line)
    
    def _draw_particles(self):
        """Draw smoke particles in 3D space.
        
        Particle positions are numpy array with shape (N, 3):
        - Column 0 (X): Width position (0-30 ft)
        - Column 1 (Y): Height position (0-20 ft) - VERTICAL
        - Column 2 (Z): Length position (0-75 ft) - depth
        
        Smoke particles should:
        - Spread horizontally (X, Z directions)
        - Rise and stratify vertically (Y direction)
        - Accumulate in hover zone (Y = 4-8 ft) and upper regions
        """
        if not self.smoke_sim:
            return
        
        particles = self.smoke_sim.get_particles()
        
        if len(particles) == 0:
            return
        
        # Extract coordinates from particle array
        xs = particles[:, 0]  # Width (X-axis)
        ys = particles[:, 1]  # Height (Y-axis) - VERTICAL
        zs = particles[:, 2]  # Length (Z-axis) - depth
        
        # Draw particles as scatter plot
        # Adjust size and alpha for better visibility
        size = PARTICLE_RENDER_SIZE * 100  # matplotlib uses different scale
        
        self._particle_scatter = self.ax.scatter(
            xs, ys, zs,
            color=COLOR_SMOKE,
            s=size,
            alpha=PARTICLE_ALPHA,
            marker='o',
            edgecolors='none',
            depthshade=True  # Add depth shading for better 3D perception
        )
    
    def mousePressEvent(self, event):
        """Handle mouse press - matplotlib handles rotation internally."""
        # Matplotlib's toolbar handles interaction
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move - matplotlib handles rotation internally."""
        # Matplotlib's toolbar handles interaction
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release - matplotlib handles rotation internally."""
        # Matplotlib's toolbar handles interaction
        super().mouseReleaseEvent(event)
    
    def wheelEvent(self, event):
        """Handle mouse wheel for zoom.
        
        Args:
            event: Wheel event
        """
        # Get current axis limits
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()
        zlim = self.ax.get_zlim()
        
        # Calculate zoom factor
        delta = event.angleDelta().y()
        zoom_factor = 1.1 if delta > 0 else 0.9
        
        # Calculate center points
        x_center = (xlim[0] + xlim[1]) / 2
        y_center = (ylim[0] + ylim[1]) / 2
        z_center = (zlim[0] + zlim[1]) / 2
        
        # Calculate new ranges
        x_range = (xlim[1] - xlim[0]) * zoom_factor / 2
        y_range = (ylim[1] - ylim[0]) * zoom_factor / 2
        z_range = (zlim[1] - zlim[0]) * zoom_factor / 2
        
        # Set new limits
        self.ax.set_xlim(x_center - x_range, x_center + x_range)
        self.ax.set_ylim(y_center - y_range, y_center + y_range)
        self.ax.set_zlim(z_center - z_range, z_center + z_range)
        
        # Refresh
        self.canvas.draw_idle()
