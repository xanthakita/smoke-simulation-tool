"""Physical constants and simulation parameters for smoke simulation."""

import numpy as np

# Room dimensions (in feet)
ROOM_WIDTH = 30.0
ROOM_LENGTH = 75.0
ROOM_HEIGHT = 20.0
ROOM_VOLUME = ROOM_WIDTH * ROOM_LENGTH * ROOM_HEIGHT  # cubic feet

# Fan specifications
FAN_DIAMETER = 28.8 / 12.0  # Convert inches to feet (2.4 ft)
FAN_RADIUS = FAN_DIAMETER / 2.0
FAN_POSITION = np.array([5.0, 15.0, 75.0])  # 5ft from left wall, 15ft up, on back wall (right side when facing from front)
FAN_MIN_SPEED = 0.0  # Percentage
FAN_MAX_SPEED = 100.0  # Percentage

# Fan performance characteristics
# Maximum CFM at 100% speed (estimated for a 28.8" industrial fan)
FAN_MAX_CFM = 8000.0  # Cubic feet per minute
FAN_MAX_VELOCITY = (FAN_MAX_CFM / 60.0) / (np.pi * FAN_RADIUS ** 2)  # ft/s at fan face

# Air properties (at room temperature ~72°F)
AIR_DENSITY = 0.075  # lb/ft³
AIR_VISCOSITY = 1.81e-5  # kg/(m·s)
AIR_TEMPERATURE = 72.0  # Fahrenheit

# Smoke properties
SMOKE_TEMPERATURE = 95.0  # Fahrenheit (warmer than ambient)
SMOKE_PARTICLE_DIAMETER = 1e-6  # meters (1 micron average)
SMOKE_DENSITY = 0.073  # lb/ft³ (slightly less than air due to temperature)

# Particle generation
PARTICLES_PER_CIGAR_PER_SECOND = 500  # Number of simulation particles per cigar per second
MAX_PARTICLES = 100000  # Maximum particles in simulation

# Physics constants
GRAVITY = 32.174  # ft/s² (downward) - NOTE: Not applied to smoke particles
BUOYANCY_FACTOR = 0.15  # Base upward force factor - modified by height-dependent multipliers
DIFFUSION_COEFFICIENT = 0.25  # ft²/s (random dispersion, multiplied by directional factors)
TIME_STEP = 0.1  # seconds per simulation step

# Height-Dependent Smoke Physics Parameters
# These parameters create realistic smoke stratification matching observed cigar lounge behavior
#
# BUOYANCY ZONES (applied as multipliers to BUOYANCY_FACTOR):
#   0-4 feet:   1.0x  - Moderate buoyancy (smoke rises from source)
#   4-8 feet:   0.05x - Very low buoyancy (HOVER ZONE - smoke lingers)
#   8-14 feet:  0.20x - Weak buoyancy (slow gradual rise)
#   14-18 feet: 0.08x - Very weak buoyancy (reaches slowly)
#   18+ feet:   0.02x - Minimal/zero buoyancy (rarely reaches ceiling)
#
# VERTICAL DAMPING ZONES (applied to vertical velocity component):
#   0-4 feet:   0.93 - Low damping (smoke rises freely)
#   4-8 feet:   0.75 - High damping (HOVER ZONE creates slowdown)
#   8-14 feet:  0.70 - Very high damping (strong slowdown)
#   14-18 feet: 0.60 - Extreme damping (much harder to reach)
#   18+ feet:   0.50 - Maximum damping (prevents ceiling rush)
#
# HORIZONTAL SPREAD PARAMETERS:
#   Initial velocity std: 2.5 ft/s (X and Z axes)
#   Diffusion multipliers: 3.5x (X and Z), 0.15x (Y)
#   Expected spread: 15-20 feet horizontal radius from each cigar
#   Horizontal damping: 0.92 (allows continued spreading)

# Sensor properties
SENSOR_DETECTION_RADIUS = 1.0  # feet (volume around sensor that detects particles)
SENSOR_RESPONSE_TIME = 1.5  # seconds (lag in sensor readings)
SENSOR_MIN_HEIGHT = 1.0  # feet (minimum height from floor)
SENSOR_MAX_HEIGHT = ROOM_HEIGHT - 1.0  # feet

# Air quality thresholds
PPM_CLEAN_AIR = 0  # No particles
PPM_GOOD = 50  # Good air quality
PPM_MODERATE = 150  # Moderate air quality
PPM_UNHEALTHY = 300  # Unhealthy air quality
PPM_VERY_UNHEALTHY = 500  # Very unhealthy
PPM_HAZARDOUS = 1000  # Hazardous

# Clarity thresholds (percentage of light transmission)
CLARITY_PERFECT = 100.0  # No smoke
CLARITY_GOOD = 85.0  # Slight haze
CLARITY_MODERATE = 60.0  # Noticeable haze
CLARITY_POOR = 40.0  # Heavy haze
CLARITY_VERY_POOR = 20.0  # Very dense smoke

# Extinction coefficient for smoke (Beer-Lambert law)
EXTINCTION_COEFFICIENT = 0.0001  # per PPM per foot

# Smoker distribution
DEFAULT_NUM_SMOKERS = 24
MAX_SMOKERS = 48
SMOKER_HEIGHT = 4.0  # feet (approximate height of cigar when sitting)

# Fan control parameters
FAN_RAMP_RATE = 10.0  # Percentage per second (how fast fan speed changes)
FAN_MIN_RUN_TIME = 30.0  # Minimum seconds to run fan once started
FAN_IDLE_THRESHOLD_PPM = 50  # PPM below which fan can turn off

# Controller PID parameters (for automatic fan control)
KP = 0.5  # Proportional gain
KI = 0.01  # Integral gain
KD = 0.1  # Derivative gain

# Simulation settings
DEFAULT_SIMULATION_SPEED = 1.0  # 1x real-time
MAX_SIMULATION_SPEED = 10.0  # 10x real-time
MIN_SIMULATION_SPEED = 0.1  # 0.1x real-time

# Visualization settings
PARTICLE_RENDER_SIZE = 0.1  # Visual size of particles in 3D view
PARTICLE_ALPHA = 0.3  # Transparency of particles
SENSOR_RENDER_SIZE = 0.5  # Size of sensor indicators
FAN_RENDER_SIZE = FAN_DIAMETER

# Data logging
DATA_LOG_INTERVAL = 1.0  # seconds between data points
MAX_GRAPH_POINTS = 1000  # Maximum points to display on graphs

# Colors (RGB tuples)
COLOR_SMOKE = (0.8, 0.8, 0.8)  # Light gray
COLOR_SENSOR_LOW = (0.0, 1.0, 0.0)  # Green
COLOR_SENSOR_HIGH = (1.0, 0.0, 0.0)  # Red
COLOR_FAN = (0.0, 0.5, 1.0)  # Blue
COLOR_ROOM = (0.95, 0.95, 0.95)  # Off-white

# File paths
CONFIG_DIR = "configs"
DATA_EXPORT_DIR = "exports"
DEFAULT_CONFIG_FILE = "default_config.json"
