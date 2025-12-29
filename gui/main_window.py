"""Main window for smoke simulation GUI."""

import sys
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QPushButton, QSpinBox, QDoubleSpinBox, QSlider, QComboBox,
    QListWidget, QListWidgetItem, QGroupBox, QRadioButton, QButtonGroup,
    QGridLayout, QSizePolicy, QFrame
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPalette, QColor
import numpy as np

from simulation.room import Room
from simulation.fan import ExhaustFan
from simulation.sensor import SensorPair
from simulation.smoke_physics import SmokeSimulation
from controllers.fan_controller import FanController, TripController
from utils.constants import (
    FAN_POSITION, ROOM_WIDTH, ROOM_LENGTH, ROOM_HEIGHT,
    DEFAULT_NUM_SMOKERS, DEFAULT_TRIP_PPM, DEFAULT_TRIP_AQI,
    DEFAULT_TRIP_DURATION
)
from utils.config_manager import ConfigManager
from visualization.renderer_3d import Renderer3D


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cigar Lounge Smoke Simulation Tool")
        self.setGeometry(100, 100, 1400, 900)
        
        # Initialize simulation components
        self.room = Room()
        self.fan = ExhaustFan()
        self.smoke_sim = SmokeSimulation(self.room, self.fan)
        
        # Initialize controllers
        self.fan_controller = FanController(self.fan)
        self.trip_controller = TripController(self.fan)
        
        # Sensor pairs
        self.sensor_pairs = []
        self.next_pair_id = 0
        
        # Config manager
        self.config_manager = ConfigManager()
        
        # Simulation state
        self.simulation_running = False
        self.simulation_time = 0.0
        self.dt = 0.1  # Time step in seconds
        
        # Create UI
        self.init_ui()
        
        # Setup simulation timer
        self.sim_timer = QTimer()
        self.sim_timer.timeout.connect(self.update_simulation)
        self.sim_timer.setInterval(int(self.dt * 1000))  # Convert to milliseconds
        
        # Setup display update timer (more frequent for smooth UI)
        self.display_timer = QTimer()
        self.display_timer.timeout.connect(self.update_display)
        self.display_timer.start(100)  # Update display 10 times per second
        
    def init_ui(self):
        """Initialize user interface."""
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # Create tabs
        self.create_simulation_tab()
        self.create_sensors_tab()
        self.create_fan_control_tab()
        
        # Status bar
        self.statusBar().showMessage("Ready")
        
    def create_simulation_tab(self):
        """Create simulation control tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 3D Visualization
        viz_group = QGroupBox("3D Smoke Simulation View")
        viz_layout = QVBoxLayout(viz_group)
        
        # Room info label
        room_info = QLabel(f"Room: {int(ROOM_WIDTH)}ft (W) × {int(ROOM_HEIGHT)}ft (H) × {int(ROOM_LENGTH)}ft (L)")
        room_info.setAlignment(Qt.AlignCenter)
        room_info.setStyleSheet("font-size: 14pt; font-weight: bold; color: white;")
        viz_layout.addWidget(room_info)
        
        # 3D Renderer
        self.renderer = Renderer3D()
        self.renderer.set_simulation_refs(self.smoke_sim, self.fan, self.sensor_pairs)
        viz_layout.addWidget(self.renderer)
        
        layout.addWidget(viz_group)
        
        # Simulation controls
        controls_group = QGroupBox("Simulation Controls")
        controls_layout = QGridLayout(controls_group)
        
        # Number of smokers
        controls_layout.addWidget(QLabel("Number of Smokers:"), 0, 0)
        self.num_smokers_spin = QSpinBox()
        self.num_smokers_spin.setRange(0, 48)
        self.num_smokers_spin.setValue(DEFAULT_NUM_SMOKERS)
        self.num_smokers_spin.valueChanged.connect(self.on_num_smokers_changed)
        controls_layout.addWidget(self.num_smokers_spin, 0, 1)
        
        # Simulation speed
        controls_layout.addWidget(QLabel("Simulation Speed:"), 1, 0)
        self.sim_speed_combo = QComboBox()
        self.sim_speed_combo.addItems(["0.5x", "1x", "2x", "5x", "10x"])
        self.sim_speed_combo.setCurrentText("1x")
        self.sim_speed_combo.currentTextChanged.connect(self.on_sim_speed_changed)
        controls_layout.addWidget(self.sim_speed_combo, 1, 1)
        
        # Start/Stop button
        self.start_stop_btn = QPushButton("Start Simulation")
        self.start_stop_btn.clicked.connect(self.toggle_simulation)
        self.start_stop_btn.setStyleSheet("font-size: 12pt; padding: 10px;")
        controls_layout.addWidget(self.start_stop_btn, 2, 0, 1, 2)
        
        # Reset button
        reset_btn = QPushButton("Reset Simulation")
        reset_btn.clicked.connect(self.reset_simulation)
        reset_btn.setStyleSheet("font-size: 12pt; padding: 10px;")
        controls_layout.addWidget(reset_btn, 3, 0, 1, 2)
        
        layout.addWidget(controls_group)
        
        # Simulation stats
        stats_group = QGroupBox("Simulation Statistics")
        stats_layout = QGridLayout(stats_group)
        
        self.time_label = QLabel("Time: 0.0 s")
        self.particles_label = QLabel("Particles: 0")
        self.fan_status_label = QLabel("Fan Speed: 0%")
        
        stats_layout.addWidget(self.time_label, 0, 0)
        stats_layout.addWidget(self.particles_label, 0, 1)
        stats_layout.addWidget(self.fan_status_label, 0, 2)
        
        layout.addWidget(stats_group)
        
        self.tabs.addTab(tab, "Simulation")
        
    def create_sensors_tab(self):
        """Create sensors configuration tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Sensor pairs list
        list_group = QGroupBox("Sensor Pairs")
        list_layout = QVBoxLayout(list_group)
        
        self.sensor_list = QListWidget()
        self.sensor_list.currentItemChanged.connect(self.on_sensor_selection_changed)
        list_layout.addWidget(self.sensor_list)
        
        # Buttons
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Add Sensor Pair")
        add_btn.clicked.connect(self.add_sensor_pair)
        remove_btn = QPushButton("Remove Selected")
        remove_btn.clicked.connect(self.remove_sensor_pair)
        
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(remove_btn)
        list_layout.addLayout(btn_layout)
        
        layout.addWidget(list_group)
        
        # Sensor configuration
        config_group = QGroupBox("Sensor Pair Configuration")
        config_layout = QGridLayout(config_group)
        
        row = 0
        
        # Sensor Wall
        config_layout.addWidget(QLabel("Sensor Wall:"), row, 0)
        self.wall_combo = QComboBox()
        self.wall_combo.addItems(["North Wall", "South Wall"])
        self.wall_combo.currentTextChanged.connect(self.on_sensor_config_changed)
        config_layout.addWidget(self.wall_combo, row, 1)
        row += 1
        
        # Distance from Fan
        config_layout.addWidget(QLabel("Distance from Fan (ft):"), row, 0)
        self.distance_spin = QDoubleSpinBox()
        self.distance_spin.setRange(0.0, ROOM_LENGTH)
        self.distance_spin.setValue(30.0)
        self.distance_spin.setSingleStep(1.0)
        self.distance_spin.valueChanged.connect(self.on_sensor_config_changed)
        config_layout.addWidget(self.distance_spin, row, 1)
        row += 1
        
        # Low Sensor Height
        config_layout.addWidget(QLabel("Low Sensor Height (ft):"), row, 0)
        self.low_height_spin = QDoubleSpinBox()
        self.low_height_spin.setRange(1.0, ROOM_HEIGHT - 1.0)
        self.low_height_spin.setValue(3.0)
        self.low_height_spin.setSingleStep(0.5)
        self.low_height_spin.valueChanged.connect(self.on_sensor_config_changed)
        config_layout.addWidget(self.low_height_spin, row, 1)
        row += 1
        
        # High Sensor Height
        config_layout.addWidget(QLabel("High Sensor Height (ft):"), row, 0)
        self.high_height_spin = QDoubleSpinBox()
        self.high_height_spin.setRange(1.0, ROOM_HEIGHT - 1.0)
        self.high_height_spin.setValue(12.0)
        self.high_height_spin.setSingleStep(0.5)
        self.high_height_spin.valueChanged.connect(self.on_sensor_config_changed)
        config_layout.addWidget(self.high_height_spin, row, 1)
        row += 1
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        config_layout.addWidget(separator, row, 0, 1, 2)
        row += 1
        
        # Trip control header
        trip_header = QLabel("Trip Control Settings")
        trip_header.setStyleSheet("font-weight: bold; font-size: 11pt;")
        config_layout.addWidget(trip_header, row, 0, 1, 2)
        row += 1
        
        # Trip PPM
        config_layout.addWidget(QLabel("Trip PPM:"), row, 0)
        self.trip_ppm_spin = QSpinBox()
        self.trip_ppm_spin.setRange(0, 1000)
        self.trip_ppm_spin.setValue(DEFAULT_TRIP_PPM)
        self.trip_ppm_spin.valueChanged.connect(self.on_sensor_config_changed)
        config_layout.addWidget(self.trip_ppm_spin, row, 1)
        row += 1
        
        # Trip AQI
        config_layout.addWidget(QLabel("Trip AQI:"), row, 0)
        self.trip_aqi_spin = QSpinBox()
        self.trip_aqi_spin.setRange(0, 500)
        self.trip_aqi_spin.setValue(DEFAULT_TRIP_AQI)
        self.trip_aqi_spin.valueChanged.connect(self.on_sensor_config_changed)
        config_layout.addWidget(self.trip_aqi_spin, row, 1)
        row += 1
        
        # Trip Duration
        config_layout.addWidget(QLabel("Trip Duration (sec):"), row, 0)
        self.trip_duration_spin = QSpinBox()
        self.trip_duration_spin.setRange(0, 3600)
        self.trip_duration_spin.setValue(DEFAULT_TRIP_DURATION)
        self.trip_duration_spin.valueChanged.connect(self.on_sensor_config_changed)
        config_layout.addWidget(self.trip_duration_spin, row, 1)
        row += 1
        
        # Separator
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.HLine)
        separator2.setFrameShadow(QFrame.Sunken)
        config_layout.addWidget(separator2, row, 0, 1, 2)
        row += 1
        
        # Trip Status Display
        status_header = QLabel("Trip Status")
        status_header.setStyleSheet("font-weight: bold; font-size: 11pt;")
        config_layout.addWidget(status_header, row, 0, 1, 2)
        row += 1
        
        self.trip_status_label = QLabel("NORMAL")
        self.trip_status_label.setAlignment(Qt.AlignCenter)
        self.trip_status_label.setStyleSheet(
            "background-color: #2ecc71; color: white; "
            "font-weight: bold; font-size: 12pt; padding: 10px; border-radius: 5px;"
        )
        config_layout.addWidget(self.trip_status_label, row, 0, 1, 2)
        row += 1
        
        self.trip_duration_label = QLabel("Remaining: 0 s")
        self.trip_duration_label.setAlignment(Qt.AlignCenter)
        config_layout.addWidget(self.trip_duration_label, row, 0, 1, 2)
        row += 1
        
        # Sensor readings display
        readings_header = QLabel("Current Readings")
        readings_header.setStyleSheet("font-weight: bold; font-size: 11pt;")
        config_layout.addWidget(readings_header, row, 0, 1, 2)
        row += 1
        
        self.low_sensor_reading_label = QLabel("Low: PPM: 0.0 | AQI: 0 | Clarity: 100%")
        config_layout.addWidget(self.low_sensor_reading_label, row, 0, 1, 2)
        row += 1
        
        self.high_sensor_reading_label = QLabel("High: PPM: 0.0 | AQI: 0 | Clarity: 100%")
        config_layout.addWidget(self.high_sensor_reading_label, row, 0, 1, 2)
        row += 1
        
        layout.addWidget(config_group)
        
        self.tabs.addTab(tab, "Sensors")
        
    def create_fan_control_tab(self):
        """Create fan control tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Fan mode selection
        mode_group = QGroupBox("Fan Control Mode")
        mode_layout = QVBoxLayout(mode_group)
        
        self.fan_mode_group = QButtonGroup()
        
        self.manual_radio = QRadioButton("Manual")
        self.manual_radio.setChecked(True)
        self.manual_radio.toggled.connect(self.on_fan_mode_changed)
        self.fan_mode_group.addButton(self.manual_radio)
        mode_layout.addWidget(self.manual_radio)
        
        self.auto_radio = QRadioButton("Auto (PID Controller)")
        self.auto_radio.toggled.connect(self.on_fan_mode_changed)
        self.fan_mode_group.addButton(self.auto_radio)
        mode_layout.addWidget(self.auto_radio)
        
        self.trip_radio = QRadioButton("Trip (Sensor-Based)")
        self.trip_radio.toggled.connect(self.on_fan_mode_changed)
        self.fan_mode_group.addButton(self.trip_radio)
        mode_layout.addWidget(self.trip_radio)
        
        layout.addWidget(mode_group)
        
        # Manual control
        manual_group = QGroupBox("Manual Speed Control")
        manual_layout = QVBoxLayout(manual_group)
        
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("Fan Speed:"))
        
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(0, 100)
        self.speed_slider.setValue(0)
        self.speed_slider.setTickPosition(QSlider.TicksBelow)
        self.speed_slider.setTickInterval(10)
        self.speed_slider.valueChanged.connect(self.on_speed_slider_changed)
        speed_layout.addWidget(self.speed_slider)
        
        self.speed_value_label = QLabel("0%")
        self.speed_value_label.setMinimumWidth(50)
        speed_layout.addWidget(self.speed_value_label)
        
        manual_layout.addLayout(speed_layout)
        
        self.manual_group_widget = manual_group
        layout.addWidget(manual_group)
        
        # Fan status
        status_group = QGroupBox("Fan Status")
        status_layout = QGridLayout(status_group)
        
        self.fan_mode_label = QLabel("Mode: Manual")
        self.fan_speed_label = QLabel("Speed: 0%")
        self.fan_cfm_label = QLabel("CFM: 0")
        self.fan_runtime_label = QLabel("Runtime: 0.0 s")
        
        status_layout.addWidget(self.fan_mode_label, 0, 0)
        status_layout.addWidget(self.fan_speed_label, 0, 1)
        status_layout.addWidget(self.fan_cfm_label, 1, 0)
        status_layout.addWidget(self.fan_runtime_label, 1, 1)
        
        layout.addWidget(status_group)
        
        # Trip controller status (only visible in Trip mode)
        trip_status_group = QGroupBox("Trip Controller Status")
        trip_status_layout = QVBoxLayout(trip_status_group)
        
        self.trip_controller_status_label = QLabel("No sensors tripped")
        trip_status_layout.addWidget(self.trip_controller_status_label)
        
        self.trip_sensors_list = QListWidget()
        self.trip_sensors_list.setMaximumHeight(150)
        trip_status_layout.addWidget(self.trip_sensors_list)
        
        self.trip_status_group_widget = trip_status_group
        self.trip_status_group_widget.setVisible(False)
        layout.addWidget(trip_status_group)
        
        layout.addStretch()
        
        self.tabs.addTab(tab, "Fan Control")
        
    def add_sensor_pair(self):
        """Add a new sensor pair."""
        wall = "south" if self.wall_combo.currentText() == "South Wall" else "north"
        
        pair = SensorPair(
            pair_id=self.next_pair_id,
            distance_from_fan=self.distance_spin.value(),
            low_height=self.low_height_spin.value(),
            high_height=self.high_height_spin.value(),
            fan_position=FAN_POSITION,
            wall=wall,
            trip_ppm=self.trip_ppm_spin.value(),
            trip_aqi=self.trip_aqi_spin.value(),
            trip_duration=self.trip_duration_spin.value()
        )
        
        self.sensor_pairs.append(pair)
        self.next_pair_id += 1
        
        # Add to controllers
        self.fan_controller.add_sensor_pair(pair)
        self.trip_controller.add_sensor_pair(pair)
        
        # Update list
        self.update_sensor_list()
        
        # Update renderer
        self.renderer.set_simulation_refs(self.smoke_sim, self.fan, self.sensor_pairs)
        
        self.statusBar().showMessage(f"Added sensor pair {pair.pair_id}")
        
    def remove_sensor_pair(self):
        """Remove selected sensor pair."""
        current_item = self.sensor_list.currentItem()
        if current_item is None:
            return
        
        pair_id = current_item.data(Qt.UserRole)
        
        # Remove from lists
        self.sensor_pairs = [sp for sp in self.sensor_pairs if sp.pair_id != pair_id]
        
        # Remove from controllers
        self.fan_controller.remove_sensor_pair(pair_id)
        self.trip_controller.remove_sensor_pair(pair_id)
        
        # Update list
        self.update_sensor_list()
        
        # Update renderer
        self.renderer.set_simulation_refs(self.smoke_sim, self.fan, self.sensor_pairs)
        
        self.statusBar().showMessage(f"Removed sensor pair {pair_id}")
        
    def update_sensor_list(self):
        """Update sensor pairs list widget."""
        self.sensor_list.clear()
        
        for pair in self.sensor_pairs:
            wall_name = "North Wall" if pair.wall == "north" else "South Wall"
            item_text = (f"Pair {pair.pair_id}: {wall_name}, "
                        f"{pair.distance_from_fan:.1f}ft from fan, "
                        f"Low:{pair.low_height:.1f}ft, High:{pair.high_height:.1f}ft")
            
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, pair.pair_id)
            self.sensor_list.addItem(item)
        
    def on_sensor_selection_changed(self, current, previous):
        """Handle sensor selection change."""
        if current is None:
            return
        
        pair_id = current.data(Qt.UserRole)
        
        # Find the sensor pair
        pair = None
        for sp in self.sensor_pairs:
            if sp.pair_id == pair_id:
                pair = sp
                break
        
        if pair is None:
            return
        
        # Update configuration fields
        self.wall_combo.blockSignals(True)
        self.distance_spin.blockSignals(True)
        self.low_height_spin.blockSignals(True)
        self.high_height_spin.blockSignals(True)
        self.trip_ppm_spin.blockSignals(True)
        self.trip_aqi_spin.blockSignals(True)
        self.trip_duration_spin.blockSignals(True)
        
        self.wall_combo.setCurrentText("North Wall" if pair.wall == "north" else "South Wall")
        self.distance_spin.setValue(pair.distance_from_fan)
        self.low_height_spin.setValue(pair.low_height)
        self.high_height_spin.setValue(pair.high_height)
        self.trip_ppm_spin.setValue(pair.trip_ppm)
        self.trip_aqi_spin.setValue(pair.trip_aqi)
        self.trip_duration_spin.setValue(pair.trip_duration)
        
        self.wall_combo.blockSignals(False)
        self.distance_spin.blockSignals(False)
        self.low_height_spin.blockSignals(False)
        self.high_height_spin.blockSignals(False)
        self.trip_ppm_spin.blockSignals(False)
        self.trip_aqi_spin.blockSignals(False)
        self.trip_duration_spin.blockSignals(False)
        
    def on_sensor_config_changed(self):
        """Handle sensor configuration change."""
        current_item = self.sensor_list.currentItem()
        if current_item is None:
            return
        
        pair_id = current_item.data(Qt.UserRole)
        
        # Find the sensor pair
        pair = None
        for sp in self.sensor_pairs:
            if sp.pair_id == pair_id:
                pair = sp
                break
        
        if pair is None:
            return
        
        # Update sensor pair configuration
        wall = "south" if self.wall_combo.currentText() == "South Wall" else "north"
        distance = self.distance_spin.value()
        low_height = self.low_height_spin.value()
        high_height = self.high_height_spin.value()
        
        # Recreate sensor pair with new settings
        new_pair = SensorPair(
            pair_id=pair_id,
            distance_from_fan=distance,
            low_height=low_height,
            high_height=high_height,
            fan_position=FAN_POSITION,
            wall=wall,
            trip_ppm=self.trip_ppm_spin.value(),
            trip_aqi=self.trip_aqi_spin.value(),
            trip_duration=self.trip_duration_spin.value()
        )
        
        # Replace in list
        for i, sp in enumerate(self.sensor_pairs):
            if sp.pair_id == pair_id:
                self.sensor_pairs[i] = new_pair
                break
        
        # Update controllers
        self.fan_controller.remove_sensor_pair(pair_id)
        self.trip_controller.remove_sensor_pair(pair_id)
        self.fan_controller.add_sensor_pair(new_pair)
        self.trip_controller.add_sensor_pair(new_pair)
        
        # Update list
        self.update_sensor_list()
        
        # Update renderer
        self.renderer.set_simulation_refs(self.smoke_sim, self.fan, self.sensor_pairs)
        
    def on_num_smokers_changed(self, value):
        """Handle number of smokers change."""
        self.smoke_sim.set_num_smokers(value)
        
    def on_sim_speed_changed(self, text):
        """Handle simulation speed change."""
        speed = float(text.replace('x', ''))
        self.dt = 0.1 * speed
        self.sim_timer.setInterval(int(0.1 * 1000 / speed))
        
    def on_fan_mode_changed(self):
        """Handle fan mode change."""
        if self.manual_radio.isChecked():
            self.fan_controller.set_mode('manual')
            self.trip_controller.set_mode('manual')
            self.manual_group_widget.setEnabled(True)
            self.trip_status_group_widget.setVisible(False)
            self.fan_mode_label.setText("Mode: Manual")
            
        elif self.auto_radio.isChecked():
            self.fan_controller.set_mode('auto')
            self.trip_controller.set_mode('manual')
            self.manual_group_widget.setEnabled(False)
            self.trip_status_group_widget.setVisible(False)
            self.fan_mode_label.setText("Mode: Auto (PID)")
            
        elif self.trip_radio.isChecked():
            self.fan_controller.set_mode('manual')
            self.trip_controller.set_mode('trip')
            self.manual_group_widget.setEnabled(False)
            self.trip_status_group_widget.setVisible(True)
            self.fan_mode_label.setText("Mode: Trip")
            
    def on_speed_slider_changed(self, value):
        """Handle manual speed slider change."""
        self.speed_value_label.setText(f"{value}%")
        if self.manual_radio.isChecked():
            self.fan.set_speed(value)
            
    def toggle_simulation(self):
        """Toggle simulation running state."""
        if self.simulation_running:
            self.stop_simulation()
        else:
            self.start_simulation()
            
    def start_simulation(self):
        """Start the simulation."""
        self.simulation_running = True
        self.start_stop_btn.setText("Stop Simulation")
        self.sim_timer.start()
        self.statusBar().showMessage("Simulation running")
        
    def stop_simulation(self):
        """Stop the simulation."""
        self.simulation_running = False
        self.start_stop_btn.setText("Start Simulation")
        self.sim_timer.stop()
        self.statusBar().showMessage("Simulation stopped")
        
    def reset_simulation(self):
        """Reset the simulation to initial state."""
        was_running = self.simulation_running
        if was_running:
            self.stop_simulation()
            
        self.simulation_time = 0.0
        self.smoke_sim.reset()
        self.fan.reset()
        self.fan_controller.reset_pid()
        self.trip_controller.reset()
        
        for pair in self.sensor_pairs:
            pair.reset()
            
        self.renderer.update()
        self.update_display()
        
        self.statusBar().showMessage("Simulation reset")
        
        if was_running:
            self.start_simulation()
            
    def update_simulation(self):
        """Update simulation step."""
        # Update simulation
        self.simulation_time += self.dt
        self.smoke_sim.update(self.dt)
        
        # Update sensors
        particles = self.smoke_sim.get_particles()
        for pair in self.sensor_pairs:
            pair.update(particles, self.dt)
            
        # Update controllers
        if self.auto_radio.isChecked():
            self.fan_controller.update(self.dt)
        elif self.trip_radio.isChecked():
            self.trip_controller.update(self.dt)
            
        # Update fan
        self.fan.update(self.dt)
        
    def update_display(self):
        """Update display elements."""
        # Update stats
        particles = self.smoke_sim.get_particles()
        num_particles = len(particles) if len(particles) > 0 else 0
        
        self.time_label.setText(f"Time: {self.simulation_time:.1f} s")
        self.particles_label.setText(f"Particles: {num_particles}")
        self.fan_status_label.setText(f"Fan Speed: {self.fan.speed_percent:.0f}%")
        
        # Update fan control tab
        self.fan_speed_label.setText(f"Speed: {self.fan.speed_percent:.0f}%")
        self.fan_cfm_label.setText(f"CFM: {self.fan.get_current_cfm():.0f}")
        self.fan_runtime_label.setText(f"Runtime: {self.fan.run_time:.1f} s")
        
        # Update sensor readings and trip status
        current_item = self.sensor_list.currentItem()
        if current_item is not None:
            pair_id = current_item.data(Qt.UserRole)
            
            for pair in self.sensor_pairs:
                if pair.pair_id == pair_id:
                    readings = pair.get_readings()
                    
                    low = readings['low']
                    high = readings['high']
                    
                    # Update reading labels with AQI
                    self.low_sensor_reading_label.setText(
                        f"Low: PPM: {low['ppm']:.1f} | AQI: {int(low['aqi'])} | Clarity: {low['clarity_percent']:.1f}%"
                    )
                    self.high_sensor_reading_label.setText(
                        f"High: PPM: {high['ppm']:.1f} | AQI: {int(high['aqi'])} | Clarity: {high['clarity_percent']:.1f}%"
                    )
                    
                    # Highlight if exceeds thresholds
                    max_ppm = max(low['ppm'], high['ppm'])
                    max_aqi = max(low['aqi'], high['aqi'])
                    
                    if max_ppm > pair.trip_ppm or max_aqi > pair.trip_aqi:
                        self.low_sensor_reading_label.setStyleSheet("color: red; font-weight: bold;")
                        self.high_sensor_reading_label.setStyleSheet("color: red; font-weight: bold;")
                    else:
                        self.low_sensor_reading_label.setStyleSheet("")
                        self.high_sensor_reading_label.setStyleSheet("")
                    
                    # Update trip status
                    if pair.is_tripped:
                        self.trip_status_label.setText("TRIPPED")
                        self.trip_status_label.setStyleSheet(
                            "background-color: #e74c3c; color: white; "
                            "font-weight: bold; font-size: 12pt; padding: 10px; border-radius: 5px;"
                        )
                        self.trip_duration_label.setText(f"Remaining: {int(pair.remaining_duration)} s")
                    else:
                        self.trip_status_label.setText("NORMAL")
                        self.trip_status_label.setStyleSheet(
                            "background-color: #2ecc71; color: white; "
                            "font-weight: bold; font-size: 12pt; padding: 10px; border-radius: 5px;"
                        )
                        self.trip_duration_label.setText("Remaining: 0 s")
                    
                    break
        
        # Update trip controller status
        if self.trip_radio.isChecked():
            status = self.trip_controller.get_status()
            
            if status['any_sensor_tripped']:
                self.trip_controller_status_label.setText(
                    f"⚠ {status['num_sensors']} sensor(s) active | "
                    f"Max Duration: {int(status['max_remaining_duration'])} s | "
                    f"Highest AQI: {int(status['highest_aqi'])}"
                )
                self.trip_controller_status_label.setStyleSheet("color: red; font-weight: bold;")
            else:
                self.trip_controller_status_label.setText("No sensors tripped")
                self.trip_controller_status_label.setStyleSheet("")
            
            # Update trip sensors list
            self.trip_sensors_list.clear()
            for sensor_status in status['sensor_statuses']:
                if sensor_status['is_tripped']:
                    item_text = (f"Pair {sensor_status['pair_id']}: "
                               f"TRIPPED - {int(sensor_status['remaining_duration'])} s remaining")
                    item = QListWidgetItem(item_text)
                    item.setForeground(QColor(231, 76, 60))  # Red
                    self.trip_sensors_list.addItem(item)
        
        # Update 3D visualization
        self.renderer.update()
