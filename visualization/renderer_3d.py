"""3D visualization renderer using PyOpenGL."""

import numpy as np
from PyQt5.QtWidgets import QOpenGLWidget
from PyQt5.QtCore import QTimer
from OpenGL.GL import *
from OpenGL.GLU import *
from utils.constants import (
    COLOR_SMOKE, COLOR_SENSOR_LOW, COLOR_SENSOR_HIGH, COLOR_FAN, COLOR_ROOM,
    PARTICLE_RENDER_SIZE, PARTICLE_ALPHA, ROOM_WIDTH, ROOM_LENGTH, ROOM_HEIGHT
)


class Renderer3D(QOpenGLWidget):
    """3D OpenGL renderer for smoke simulation."""
    
    def __init__(self, parent=None):
        """Initialize 3D renderer.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Camera settings
        self.camera_distance = 100.0
        self.camera_rotation_x = 30.0
        self.camera_rotation_y = -45.0
        self.camera_target = np.array([ROOM_WIDTH/2, ROOM_HEIGHT/2, ROOM_LENGTH/2])
        
        # Mouse interaction
        self.last_mouse_pos = None
        
        # Simulation references (set externally)
        self.smoke_sim = None
        self.fan = None
        self.sensor_pairs = []
        
        # Rendering options
        self.show_particles = True
        self.show_sensors = True
        self.show_fan = True
        self.show_room = True
        
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
    
    def initializeGL(self):
        """Initialize OpenGL settings."""
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_POINT_SMOOTH)
        glClearColor(0.1, 0.1, 0.15, 1.0)
        
        # Lighting
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glLightfv(GL_LIGHT0, GL_POSITION, [1, 1, 1, 0])
        glLightfv(GL_LIGHT0, GL_AMBIENT, [0.3, 0.3, 0.3, 1.0])
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.8, 0.8, 0.8, 1.0])
    
    def resizeGL(self, width, height):
        """Handle window resize.
        
        Args:
            width: New width
            height: New height
        """
        if height == 0:
            height = 1
        
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45.0, width / height, 0.1, 500.0)
        glMatrixMode(GL_MODELVIEW)
    
    def paintGL(self):
        """Render the scene."""
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        
        # Set up camera
        camera_pos = self._calculate_camera_position()
        gluLookAt(
            camera_pos[0], camera_pos[1], camera_pos[2],
            self.camera_target[0], self.camera_target[1], self.camera_target[2],
            0, 1, 0
        )
        
        # Draw scene
        if self.show_room:
            self._draw_room()
        
        if self.show_fan and self.fan:
            self._draw_fan()
        
        if self.show_sensors:
            self._draw_sensors()
        
        if self.show_particles and self.smoke_sim:
            self._draw_particles()
    
    def _calculate_camera_position(self):
        """Calculate camera position based on rotation and distance.
        
        Returns:
            numpy array with camera position
        """
        # Convert angles to radians
        rot_x = np.radians(self.camera_rotation_x)
        rot_y = np.radians(self.camera_rotation_y)
        
        # Calculate position
        x = self.camera_distance * np.cos(rot_x) * np.cos(rot_y)
        y = self.camera_distance * np.sin(rot_x)
        z = self.camera_distance * np.cos(rot_x) * np.sin(rot_y)
        
        return self.camera_target + np.array([x, y, z])
    
    def _draw_room(self):
        """Draw room boundaries."""
        glDisable(GL_LIGHTING)
        glLineWidth(2.0)
        glColor3f(*COLOR_ROOM)
        
        # Draw wireframe box
        glBegin(GL_LINES)
        
        # Bottom rectangle
        glVertex3f(0, 0, 0)
        glVertex3f(ROOM_WIDTH, 0, 0)
        
        glVertex3f(ROOM_WIDTH, 0, 0)
        glVertex3f(ROOM_WIDTH, 0, ROOM_LENGTH)
        
        glVertex3f(ROOM_WIDTH, 0, ROOM_LENGTH)
        glVertex3f(0, 0, ROOM_LENGTH)
        
        glVertex3f(0, 0, ROOM_LENGTH)
        glVertex3f(0, 0, 0)
        
        # Top rectangle
        glVertex3f(0, ROOM_HEIGHT, 0)
        glVertex3f(ROOM_WIDTH, ROOM_HEIGHT, 0)
        
        glVertex3f(ROOM_WIDTH, ROOM_HEIGHT, 0)
        glVertex3f(ROOM_WIDTH, ROOM_HEIGHT, ROOM_LENGTH)
        
        glVertex3f(ROOM_WIDTH, ROOM_HEIGHT, ROOM_LENGTH)
        glVertex3f(0, ROOM_HEIGHT, ROOM_LENGTH)
        
        glVertex3f(0, ROOM_HEIGHT, ROOM_LENGTH)
        glVertex3f(0, ROOM_HEIGHT, 0)
        
        # Vertical edges
        glVertex3f(0, 0, 0)
        glVertex3f(0, ROOM_HEIGHT, 0)
        
        glVertex3f(ROOM_WIDTH, 0, 0)
        glVertex3f(ROOM_WIDTH, ROOM_HEIGHT, 0)
        
        glVertex3f(ROOM_WIDTH, 0, ROOM_LENGTH)
        glVertex3f(ROOM_WIDTH, ROOM_HEIGHT, ROOM_LENGTH)
        
        glVertex3f(0, 0, ROOM_LENGTH)
        glVertex3f(0, ROOM_HEIGHT, ROOM_LENGTH)
        
        glEnd()
        
        # Draw floor grid
        glColor4f(0.3, 0.3, 0.35, 0.3)
        glBegin(GL_LINES)
        for i in range(0, int(ROOM_WIDTH) + 1, 5):
            glVertex3f(i, 0, 0)
            glVertex3f(i, 0, ROOM_LENGTH)
        for i in range(0, int(ROOM_LENGTH) + 1, 5):
            glVertex3f(0, 0, i)
            glVertex3f(ROOM_WIDTH, 0, i)
        glEnd()
        
        glEnable(GL_LIGHTING)
    
    def _draw_fan(self):
        """Draw exhaust fan."""
        if not self.fan:
            return
        
        glDisable(GL_LIGHTING)
        
        pos = self.fan.position
        radius = self.fan.radius
        
        # Fan color based on speed
        intensity = self.fan.speed_percent / 100.0
        color = (COLOR_FAN[0] * intensity, COLOR_FAN[1] * intensity, COLOR_FAN[2] * intensity)
        glColor3f(*color)
        
        # Draw fan circle
        segments = 20
        glBegin(GL_LINE_LOOP)
        for i in range(segments):
            angle = 2.0 * np.pi * i / segments
            x = pos[0] + radius * np.cos(angle)
            y = pos[1] + radius * np.sin(angle)
            glVertex3f(x, y, pos[2])
        glEnd()
        
        # Draw fan blades
        glBegin(GL_LINES)
        for i in range(4):
            angle = 2.0 * np.pi * i / 4
            x = pos[0] + radius * np.cos(angle)
            y = pos[1] + radius * np.sin(angle)
            glVertex3f(pos[0], pos[1], pos[2])
            glVertex3f(x, y, pos[2])
        glEnd()
        
        glEnable(GL_LIGHTING)
    
    def _draw_sensors(self):
        """Draw sensor positions."""
        glDisable(GL_LIGHTING)
        
        for pair in self.sensor_pairs:
            # Draw low sensor (green)
            low_pos = pair.low_sensor.position
            glColor3f(*COLOR_SENSOR_LOW)
            self._draw_cube(low_pos, 0.5)
            
            # Draw high sensor (red)
            high_pos = pair.high_sensor.position
            glColor3f(*COLOR_SENSOR_HIGH)
            self._draw_cube(high_pos, 0.5)
            
            # Draw line connecting pair
            glColor4f(1.0, 1.0, 1.0, 0.3)
            glBegin(GL_LINES)
            glVertex3f(*low_pos)
            glVertex3f(*high_pos)
            glEnd()
        
        glEnable(GL_LIGHTING)
    
    def _draw_cube(self, position, size):
        """Draw a small cube at position.
        
        Args:
            position: numpy array [x, y, z]
            size: Size of cube
        """
        x, y, z = position
        s = size / 2
        
        glBegin(GL_LINE_LOOP)
        glVertex3f(x-s, y-s, z-s)
        glVertex3f(x+s, y-s, z-s)
        glVertex3f(x+s, y+s, z-s)
        glVertex3f(x-s, y+s, z-s)
        glEnd()
        
        glBegin(GL_LINE_LOOP)
        glVertex3f(x-s, y-s, z+s)
        glVertex3f(x+s, y-s, z+s)
        glVertex3f(x+s, y+s, z+s)
        glVertex3f(x-s, y+s, z+s)
        glEnd()
        
        glBegin(GL_LINES)
        glVertex3f(x-s, y-s, z-s)
        glVertex3f(x-s, y-s, z+s)
        glVertex3f(x+s, y-s, z-s)
        glVertex3f(x+s, y-s, z+s)
        glVertex3f(x+s, y+s, z-s)
        glVertex3f(x+s, y+s, z+s)
        glVertex3f(x-s, y+s, z-s)
        glVertex3f(x-s, y+s, z+s)
        glEnd()
    
    def _draw_particles(self):
        """Draw smoke particles."""
        if not self.smoke_sim:
            return
        
        particles = self.smoke_sim.get_particles()
        
        if len(particles) == 0:
            return
        
        glDisable(GL_LIGHTING)
        glPointSize(PARTICLE_RENDER_SIZE * 10)
        
        glBegin(GL_POINTS)
        glColor4f(*COLOR_SMOKE, PARTICLE_ALPHA)
        
        for particle in particles:
            glVertex3f(*particle)
        
        glEnd()
        
        glEnable(GL_LIGHTING)
    
    def mousePressEvent(self, event):
        """Handle mouse press for camera rotation.
        
        Args:
            event: Mouse event
        """
        self.last_mouse_pos = event.pos()
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for camera rotation.
        
        Args:
            event: Mouse event
        """
        if self.last_mouse_pos is not None:
            dx = event.x() - self.last_mouse_pos.x()
            dy = event.y() - self.last_mouse_pos.y()
            
            self.camera_rotation_y += dx * 0.5
            self.camera_rotation_x += dy * 0.5
            
            # Clamp vertical rotation
            self.camera_rotation_x = np.clip(self.camera_rotation_x, -89, 89)
            
            self.last_mouse_pos = event.pos()
            self.update()
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release.
        
        Args:
            event: Mouse event
        """
        self.last_mouse_pos = None
    
    def wheelEvent(self, event):
        """Handle mouse wheel for zoom.
        
        Args:
            event: Wheel event
        """
        delta = event.angleDelta().y()
        self.camera_distance -= delta * 0.1
        self.camera_distance = np.clip(self.camera_distance, 20.0, 300.0)
        self.update()
