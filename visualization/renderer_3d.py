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
        
        COORDINATE SYSTEM & MATPLOTLIB MAPPING:
        =======================================
        Data is stored as [x, y, z] where:
          - x (index 0): Width (0-30 ft)
          - y (index 1): Height (0-20 ft)
          - z (index 2): Length (0-75 ft)
        
        Matplotlib 3D axes have Z as VERTICAL by default, so we swap Y and Z:
          - matplotlib X-axis (horizontal): Width (0-30 ft) ← data[0]
          - matplotlib Y-axis (depth): Length (0-75 ft) ← data[2]
          - matplotlib Z-axis (VERTICAL): Height (0-20 ft) ← data[1]
        """
        # Set axis limits with Y and Z swapped for matplotlib
        self.ax.set_xlim(0, ROOM_WIDTH)   # X: Width (0-30 ft)
        self.ax.set_ylim(0, ROOM_LENGTH)  # Y: Length (0-75 ft, depth)
        self.ax.set_zlim(0, ROOM_HEIGHT)  # Z: Height (0-20 ft, VERTICAL)
        
        # Set labels (matplotlib Y is depth, Z is vertical)
        self.ax.set_xlabel('Width (ft)', color='white', fontsize=10, labelpad=8)
        self.ax.set_ylabel('Length (ft)', color='white', fontsize=10, labelpad=8)  # Depth
        self.ax.set_zlabel('Height (ft)', color='white', fontsize=10, labelpad=8)  # Vertical
        
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
        
        # Set initial view angle to show room upright with height vertical
        # elevation=20: look down from slightly above
        # azimuth=-60: view from front-left corner (shows width, height, and depth)
        self.ax.view_init(elev=self.camera_elevation, azim=self.camera_azimuth)
        
        # Force equal aspect ratio to prevent distortion
        # matplotlib axes are [X, Y, Z] = [Width, Length, Height]
        try:
            self.ax.set_box_aspect([ROOM_WIDTH, ROOM_LENGTH, ROOM_HEIGHT])
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
        """Draw room boundaries with Y/Z swapped for matplotlib.
        
        Data: [x, y, z] = [Width, Height, Length]
        Plot to matplotlib with Y/Z swapped: [x, z, y]
        - matplotlib X: Width
        - matplotlib Y: Length (depth)
        - matplotlib Z: Height (VERTICAL)
        """
        if self._room_lines is not None:
            return  # Already drawn
        
        # Define room corners in DATA coords [x, y, z]  = [Width, Height, Length]
        # Convert to matplotlib coords [X, Y, Z] by swapping y and z
        def to_mpl(x, y, z):
            """Convert data [x, y, z] to matplotlib [X, Y, Z] = [x, z, y]"""
            return (x, z, y)
        
        # FLOOR (data y=0, all corners at ground level)
        floor_corners = [
            to_mpl(0, 0, 0),                      # Front-left-bottom
            to_mpl(ROOM_WIDTH, 0, 0),             # Front-right-bottom
            to_mpl(ROOM_WIDTH, 0, ROOM_LENGTH),   # Back-right-bottom
            to_mpl(0, 0, ROOM_LENGTH),            # Back-left-bottom
        ]
        
        # CEILING (data y=ROOM_HEIGHT, all corners at ceiling)
        ceiling_corners = [
            to_mpl(0, ROOM_HEIGHT, 0),
            to_mpl(ROOM_WIDTH, ROOM_HEIGHT, 0),
            to_mpl(ROOM_WIDTH, ROOM_HEIGHT, ROOM_LENGTH),
            to_mpl(0, ROOM_HEIGHT, ROOM_LENGTH),
        ]
        
        # Draw floor edges
        for i in range(4):
            next_i = (i + 1) % 4
            x1, y1, z1 = floor_corners[i]
            x2, y2, z2 = floor_corners[next_i]
            line = self.ax.plot([x1, x2], [y1, y2], [z1, z2], 
                               color=COLOR_ROOM, linewidth=2, alpha=0.7)[0]
            if self._room_lines is None:
                self._room_lines = [line]
            else:
                self._room_lines.append(line)
        
        # Draw ceiling edges
        for i in range(4):
            next_i = (i + 1) % 4
            x1, y1, z1 = ceiling_corners[i]
            x2, y2, z2 = ceiling_corners[next_i]
            line = self.ax.plot([x1, x2], [y1, y2], [z1, z2],
                               color=COLOR_ROOM, linewidth=2, alpha=0.7)[0]
            self._room_lines.append(line)
        
        # Draw vertical edges connecting floor to ceiling
        for i in range(4):
            x1, y1, z1 = floor_corners[i]
            x2, y2, z2 = ceiling_corners[i]
            line = self.ax.plot([x1, x2], [y1, y2], [z1, z2],
                               color=COLOR_ROOM, linewidth=2, alpha=0.7)[0]
            self._room_lines.append(line)
        
        # Draw floor grid (at floor level, data y=0, matplotlib z=0)
        grid_spacing = 5
        
        # Grid lines parallel to Length (data z-axis) at regular Width intervals
        for i in range(0, int(ROOM_WIDTH) + 1, grid_spacing):
            x1, y1, z1 = to_mpl(i, 0, 0)
            x2, y2, z2 = to_mpl(i, 0, ROOM_LENGTH)
            line = self.ax.plot([x1, x2], [y1, y2], [z1, z2],
                               color='#4a4a55', linewidth=0.5, alpha=0.3)[0]
            self._room_lines.append(line)
        
        # Grid lines parallel to Width (data x-axis) at regular Length intervals
        for i in range(0, int(ROOM_LENGTH) + 1, grid_spacing):
            x1, y1, z1 = to_mpl(0, 0, i)
            x2, y2, z2 = to_mpl(ROOM_WIDTH, 0, i)
            line = self.ax.plot([x1, x2], [y1, y2], [z1, z2],
                               color='#4a4a55', linewidth=0.5, alpha=0.3)[0]
            self._room_lines.append(line)
    
    def _draw_fan(self):
        """Draw exhaust fan with Y/Z swapped for matplotlib.
        
        Fan position in data: [x, y, z] = [Width, Height, Length]
        Plot to matplotlib: [X, Y, Z] = [x, z, y] (swap y and z)
        
        Fan orientation depends on which wall it's mounted on:
        - North wall (x ≈ 0): Circle in YZ plane (varies in Y and Z, constant X)
        - South wall (x ≈ ROOM_WIDTH): Circle in YZ plane (varies in Y and Z, constant X)
        - West wall (z ≈ ROOM_LENGTH): Circle in XY plane (varies in X and Y, constant Z)
        - East wall (z ≈ 0): Circle in XY plane (varies in X and Y, constant Z)
        """
        if not self.fan:
            return
        
        pos = self.fan.position  # [x, y, z] = [Width, Height, Length]
        radius = self.fan.radius
        
        # Convert to matplotlib coords (swap y and z)
        mpl_x = pos[0]  # Width → X
        mpl_y = pos[2]  # Length → Y (depth)
        mpl_z = pos[1]  # Height → Z (vertical)
        
        # Fan color based on speed
        intensity = self.fan.speed_percent / 100.0
        color = (
            COLOR_FAN[0] * (0.3 + 0.7 * intensity),
            COLOR_FAN[1] * (0.3 + 0.7 * intensity),
            COLOR_FAN[2] * (0.3 + 0.7 * intensity)
        )
        
        # Determine which wall the fan is on based on position
        # Check if fan is on North/South wall (x near 0 or ROOM_WIDTH)
        on_north_wall = pos[0] < 2.0  # Within 2 feet of North wall (x≈0)
        on_south_wall = pos[0] > ROOM_WIDTH - 2.0  # Within 2 feet of South wall (x≈30)
        
        segments = 24
        angles = np.linspace(0, 2 * np.pi, segments + 1)
        
        if on_north_wall or on_south_wall:
            # Fan on North or South wall - circle in YZ plane (matplotlib Y and Z)
            # Circle varies in depth (Y) and height (Z), constant width (X)
            circle_y = mpl_y + radius * np.cos(angles)  # Depth
            circle_z = mpl_z + radius * np.sin(angles)  # Vertical
            circle_x = np.full(segments + 1, mpl_x)      # Width constant at wall
            
            line = self.ax.plot(circle_x, circle_y, circle_z, color=color, linewidth=2.5)[0]
            self._fan_artists.append(line)
            
            # Draw fan blades (4 spokes)
            for i in range(4):
                angle = 2.0 * np.pi * i / 4
                end_y = mpl_y + radius * np.cos(angle)
                end_z = mpl_z + radius * np.sin(angle)
                line = self.ax.plot(
                    [mpl_x, mpl_x],    # X constant at wall
                    [mpl_y, end_y],    # Y from center to edge
                    [mpl_z, end_z],    # Z from center to edge
                    color=color, linewidth=2.5
                )[0]
                self._fan_artists.append(line)
        else:
            # Fan on East or West wall - circle in XZ plane (matplotlib X and Z)
            # Circle varies in width (X) and height (Z), constant depth (Y)
            circle_x = mpl_x + radius * np.cos(angles)  # Horizontal
            circle_z = mpl_z + radius * np.sin(angles)  # Vertical
            circle_y = np.full(segments + 1, mpl_y)      # Depth constant at wall
            
            line = self.ax.plot(circle_x, circle_y, circle_z, color=color, linewidth=2.5)[0]
            self._fan_artists.append(line)
            
            # Draw fan blades (4 spokes)
            for i in range(4):
                angle = 2.0 * np.pi * i / 4
                end_x = mpl_x + radius * np.cos(angle)
                end_z = mpl_z + radius * np.sin(angle)
                line = self.ax.plot(
                    [mpl_x, end_x],    # X from center to edge
                    [mpl_y, mpl_y],    # Y constant at wall
                    [mpl_z, end_z],    # Z from center to edge
                    color=color, linewidth=2.5
                )[0]
                self._fan_artists.append(line)
        
        # Draw center point
        scatter = self.ax.scatter([mpl_x], [mpl_y], [mpl_z], 
                                 color=color, s=50, marker='o', edgecolors='white', linewidths=1)
        self._fan_artists.append(scatter)
    
    def _draw_sensors(self):
        """Draw sensor positions with Y/Z swapped for matplotlib.
        
        Sensor positions in data: [x, y, z] = [Width, Height, Length]
        Sensors in pairs (low/high) with different y (height) values
        """
        for pair in self.sensor_pairs:
            # Get low sensor position and convert to matplotlib coords
            low_pos = pair.low_sensor.position  # [x, y, z]
            low_mpl_x = low_pos[0]  # Width → X
            low_mpl_y = low_pos[2]  # Length → Y (depth)
            low_mpl_z = low_pos[1]  # Height → Z (vertical)
            
            # Draw low sensor (green square)
            scatter = self.ax.scatter(
                [low_mpl_x], [low_mpl_y], [low_mpl_z],
                color=COLOR_SENSOR_LOW, s=120, marker='s',
                edgecolors='white', linewidths=1.5, alpha=0.9
            )
            self._sensor_artists.append(scatter)
            
            # Get high sensor position and convert to matplotlib coords
            high_pos = pair.high_sensor.position  # [x, y, z]
            high_mpl_x = high_pos[0]  # Width → X
            high_mpl_y = high_pos[2]  # Length → Y (depth)
            high_mpl_z = high_pos[1]  # Height → Z (vertical)
            
            # Draw high sensor (red square)
            scatter = self.ax.scatter(
                [high_mpl_x], [high_mpl_y], [high_mpl_z],
                color=COLOR_SENSOR_HIGH, s=120, marker='s',
                edgecolors='white', linewidths=1.5, alpha=0.9
            )
            self._sensor_artists.append(scatter)
            
            # Draw vertical line connecting pair (same X,Y but different Z in matplotlib)
            line = self.ax.plot(
                [low_mpl_x, high_mpl_x],  # X coordinates
                [low_mpl_y, high_mpl_y],  # Y coordinates (depth)
                [low_mpl_z, high_mpl_z],  # Z coordinates (vertical line)
                color='white', linewidth=1.5, alpha=0.4, linestyle='--'
            )[0]
            self._sensor_artists.append(line)
    
    def _draw_particles(self):
        """Draw smoke particles with Y/Z swapped for matplotlib.
        
        Particle positions in data: (N, 3) array of [x, y, z]
        - x (column 0): Width (0-30 ft)
        - y (column 1): Height (0-20 ft)
        - z (column 2): Length (0-75 ft)
        
        Plot to matplotlib with Y/Z swapped:
        - matplotlib X ← particles[:, 0] (Width)
        - matplotlib Y ← particles[:, 2] (Length, depth)
        - matplotlib Z ← particles[:, 1] (Height, VERTICAL)
        """
        if not self.smoke_sim:
            return
        
        particles = self.smoke_sim.get_particles()
        
        if len(particles) == 0:
            return
        
        # Extract and swap Y/Z coordinates for matplotlib
        mpl_xs = particles[:, 0]  # Width → X
        mpl_ys = particles[:, 2]  # Length → Y (depth)
        mpl_zs = particles[:, 1]  # Height → Z (VERTICAL)
        
        # Draw particles as scatter plot
        size = PARTICLE_RENDER_SIZE * 100  # matplotlib uses different scale
        
        self._particle_scatter = self.ax.scatter(
            mpl_xs, mpl_ys, mpl_zs,
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
