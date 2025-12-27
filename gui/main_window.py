"""Main GUI window for smoke simulation application."""

import sys
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QSpinBox, QDoubleSpinBox, QSlider, QComboBox,
    QGroupBox, QTextEdit, QTabWidget, QFileDialog, QMessageBox,
    QListWidget, QSplitter
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont
import pyqtgraph as pg
import numpy as np

from simulation.room import Room
from simulation.fan import ExhaustFan
from simulation.sensor import SensorPair
from simulation.smoke_physics import SmokeSimulation
from controllers.fan_controller import FanController
from data.data_logger import DataLogger
from visualization.renderer_3d import Renderer3D
from utils.config_manager import ConfigManager
from utils.constants import (
    MAX_SMOKERS, DEFAULT_NUM_SMOKERS, FAN_POSITION,
    DEFAULT_SIMULATION_SPEED, MAX_SIMULATION_SPEED, MIN_SIMULATION_SPEED
)


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        """Initialize main window."""
        super().__init__()
        
        self.setWindowTitle("Cigar Lounge Smoke Simulation Tool")
        self.setGeometry(100, 100, 1600, 900)
        
        # Initialize simulation components
        self.room = Room()
        self.fan = ExhaustFan()
        self.smoke_sim = SmokeSimulation(self.room, self.fan)
        self.fan_controller = FanController(self.fan)
        self.data_logger = DataLogger()
        self.config_manager = ConfigManager()
        
        # Sensor pairs
        self.sensor_pairs = []
        
        # Simulation state
        self.is_running = False
        self.simulation_time = 0.0
        self.simulation_speed = DEFAULT_SIMULATION_SPEED
        
        # Setup UI
        self._setup_ui()
        
        # Setup timer for simulation updates
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_simulation)
        self.timer.setInterval(33)  # ~30 FPS
        
        # Setup timer for display updates (slower)
        self.display_timer = QTimer()
        self.display_timer.timeout.connect(self._update_displays)
        self.display_timer.start(100)  # 10 Hz
        
    def _setup_ui(self):
        """Setup the user interface."""
        # Central widget with splitter
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        
        # Create main splitter
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel - 3D view and controls
        left_panel = self._create_left_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - data and graphs
        right_panel = self._create_right_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter proportions
        splitter.setSizes([800, 800])
    
    def _create_left_panel(self):
        """Create left panel with 3D view and controls.
        
        Returns:
            QWidget containing left panel
        """
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 3D View
        self.renderer_3d = Renderer3D()
        self.renderer_3d.set_simulation_refs(self.smoke_sim, self.fan, self.sensor_pairs)
        self.renderer_3d.setMinimumHeight(400)
        layout.addWidget(self.renderer_3d, stretch=2)
        
        # Control tabs
        control_tabs = QTabWidget()
        control_tabs.addTab(self._create_simulation_controls(), "Simulation")
        control_tabs.addTab(self._create_sensor_controls(), "Sensors")
        control_tabs.addTab(self._create_fan_controls(), "Fan Control")
        layout.addWidget(control_tabs, stretch=1)
        
        return panel
    
    def _create_right_panel(self):
        """Create right panel with data display and graphs.
        
        Returns:
            QWidget containing right panel
        """
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Data tabs
        data_tabs = QTabWidget()
        data_tabs.addTab(self._create_sensor_data_panel(), "Sensor Readings")
        data_tabs.addTab(self._create_graphs_panel(), "Graphs")
        data_tabs.addTab(self._create_statistics_panel(), "Statistics")
        layout.addWidget(data_tabs)
        
        return panel
    
    def _create_simulation_controls(self):
        """Create simulation control panel.
        
        Returns:
            QWidget with simulation controls
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Play/Pause/Reset buttons
        button_layout = QHBoxLayout()
        
        self.btn_start = QPushButton("Start")
        self.btn_start.clicked.connect(self._start_simulation)
        button_layout.addWidget(self.btn_start)
        
        self.btn_pause = QPushButton("Pause")
        self.btn_pause.clicked.connect(self._pause_simulation)
        self.btn_pause.setEnabled(False)
        button_layout.addWidget(self.btn_pause)
        
        self.btn_reset = QPushButton("Reset")
        self.btn_reset.clicked.connect(self._reset_simulation)
        button_layout.addWidget(self.btn_reset)
        
        layout.addLayout(button_layout)
        
        # Number of smokers
        smoker_group = QGroupBox("Smoke Sources")
        smoker_layout = QGridLayout()
        
        smoker_layout.addWidget(QLabel("Number of Smokers:"), 0, 0)
        self.spin_smokers = QSpinBox()
        self.spin_smokers.setRange(0, MAX_SMOKERS)
        self.spin_smokers.setValue(DEFAULT_NUM_SMOKERS)
        self.spin_smokers.valueChanged.connect(self._update_num_smokers)
        smoker_layout.addWidget(self.spin_smokers, 0, 1)
        
        smoker_group.setLayout(smoker_layout)
        layout.addWidget(smoker_group)
        
        # Simulation speed
        speed_group = QGroupBox("Simulation Speed")
        speed_layout = QGridLayout()
        
        speed_layout.addWidget(QLabel("Speed Multiplier:"), 0, 0)
        self.spin_speed = QDoubleSpinBox()
        self.spin_speed.setRange(MIN_SIMULATION_SPEED, MAX_SIMULATION_SPEED)
        self.spin_speed.setValue(DEFAULT_SIMULATION_SPEED)
        self.spin_speed.setSingleStep(0.5)
        self.spin_speed.valueChanged.connect(self._update_simulation_speed)
        speed_layout.addWidget(self.spin_speed, 0, 1)
        
        speed_group.setLayout(speed_layout)
        layout.addWidget(speed_group)
        
        # Configuration
        config_group = QGroupBox("Configuration")
        config_layout = QVBoxLayout()
        
        btn_save_config = QPushButton("Save Configuration")
        btn_save_config.clicked.connect(self._save_configuration)
        config_layout.addWidget(btn_save_config)
        
        btn_load_config = QPushButton("Load Configuration")
        btn_load_config.clicked.connect(self._load_configuration)
        config_layout.addWidget(btn_load_config)
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        layout.addStretch()
        
        return widget
    
    def _create_sensor_controls(self):
        """Create sensor configuration panel.
        
        Returns:
            QWidget with sensor controls
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Sensor list
        list_layout = QHBoxLayout()
        self.sensor_list = QListWidget()
        list_layout.addWidget(self.sensor_list)
        
        # Buttons
        btn_layout = QVBoxLayout()
        btn_add = QPushButton("Add Sensor Pair")
        btn_add.clicked.connect(self._add_sensor_pair)
        btn_layout.addWidget(btn_add)
        
        btn_remove = QPushButton("Remove Selected")
        btn_remove.clicked.connect(self._remove_sensor_pair)
        btn_layout.addWidget(btn_remove)
        
        btn_layout.addStretch()
        list_layout.addLayout(btn_layout)
        
        layout.addLayout(list_layout)
        
        # Sensor configuration
        config_group = QGroupBox("Sensor Pair Configuration")
        config_layout = QGridLayout()
        
        config_layout.addWidget(QLabel("Distance from Fan (ft):"), 0, 0)
        self.spin_sensor_distance = QDoubleSpinBox()
        self.spin_sensor_distance.setRange(1.0, 70.0)
        self.spin_sensor_distance.setValue(30.0)
        self.spin_sensor_distance.setSingleStep(1.0)
        config_layout.addWidget(self.spin_sensor_distance, 0, 1)
        
        config_layout.addWidget(QLabel("Low Sensor Height (ft):"), 1, 0)
        self.spin_low_height = QDoubleSpinBox()
        self.spin_low_height.setRange(1.0, 19.0)
        self.spin_low_height.setValue(3.0)
        self.spin_low_height.setSingleStep(0.5)
        config_layout.addWidget(self.spin_low_height, 1, 1)
        
        config_layout.addWidget(QLabel("High Sensor Height (ft):"), 2, 0)
        self.spin_high_height = QDoubleSpinBox()
        self.spin_high_height.setRange(2.0, 19.0)
        self.spin_high_height.setValue(12.0)
        self.spin_high_height.setSingleStep(0.5)
        config_layout.addWidget(self.spin_high_height, 2, 1)
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        layout.addStretch()
        
        return widget
    
    def _create_fan_controls(self):
        """Create fan control panel.
        
        Returns:
            QWidget with fan controls
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Fan mode
        mode_group = QGroupBox("Fan Mode")
        mode_layout = QVBoxLayout()
        
        self.combo_fan_mode = QComboBox()
        self.combo_fan_mode.addItems(["Manual", "Automatic"])
        self.combo_fan_mode.currentTextChanged.connect(self._change_fan_mode)
        mode_layout.addWidget(self.combo_fan_mode)
        
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)
        
        # Manual speed control
        self.manual_speed_group = QGroupBox("Manual Speed Control")
        manual_layout = QVBoxLayout()
        
        self.slider_fan_speed = QSlider(Qt.Horizontal)
        self.slider_fan_speed.setRange(0, 100)
        self.slider_fan_speed.setValue(0)
        self.slider_fan_speed.valueChanged.connect(self._manual_fan_speed_changed)
        manual_layout.addWidget(self.slider_fan_speed)
        
        self.label_fan_speed = QLabel("Fan Speed: 0%")
        manual_layout.addWidget(self.label_fan_speed)
        
        self.manual_speed_group.setLayout(manual_layout)
        layout.addWidget(self.manual_speed_group)
        
        # Fan info
        info_group = QGroupBox("Fan Information")
        info_layout = QVBoxLayout()
        
        self.label_fan_info = QLabel()
        self.label_fan_info.setFont(QFont("Courier", 9))
        self.label_fan_info.setWordWrap(True)
        info_layout.addWidget(self.label_fan_info)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        layout.addStretch()
        
        return widget
    
    def _create_sensor_data_panel(self):
        """Create sensor data display panel.
        
        Returns:
            QWidget with sensor data
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.text_sensor_data = QTextEdit()
        self.text_sensor_data.setReadOnly(True)
        self.text_sensor_data.setFont(QFont("Courier", 9))
        layout.addWidget(self.text_sensor_data)
        
        return widget
    
    def _create_graphs_panel(self):
        """Create graphs panel.
        
        Returns:
            QWidget with graphs
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # PPM graph
        self.graph_ppm = pg.PlotWidget(title="Particle Concentration (PPM)")
        self.graph_ppm.setLabel('left', 'PPM')
        self.graph_ppm.setLabel('bottom', 'Time', units='s')
        self.graph_ppm.addLegend()
        layout.addWidget(self.graph_ppm)
        
        # Clarity graph
        self.graph_clarity = pg.PlotWidget(title="Air Clarity (%)")
        self.graph_clarity.setLabel('left', 'Clarity', units='%')
        self.graph_clarity.setLabel('bottom', 'Time', units='s')
        self.graph_clarity.addLegend()
        layout.addWidget(self.graph_clarity)
        
        # Fan speed graph
        self.graph_fan = pg.PlotWidget(title="Fan Speed (%)")
        self.graph_fan.setLabel('left', 'Speed', units='%')
        self.graph_fan.setLabel('bottom', 'Time', units='s')
        layout.addWidget(self.graph_fan)
        
        return widget
    
    def _create_statistics_panel(self):
        """Create statistics panel.
        
        Returns:
            QWidget with statistics
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.text_statistics = QTextEdit()
        self.text_statistics.setReadOnly(True)
        self.text_statistics.setFont(QFont("Courier", 10))
        layout.addWidget(self.text_statistics)
        
        # Export button
        btn_export = QPushButton("Export Data to CSV")
        btn_export.clicked.connect(self._export_data)
        layout.addWidget(btn_export)
        
        return widget
    
    def _start_simulation(self):
        """Start the simulation."""
        self.is_running = True
        self.btn_start.setEnabled(False)
        self.btn_pause.setEnabled(True)
        self.timer.start()
        
        # Initialize smokers if not already done
        if self.smoke_sim.num_smokers == 0:
            self._update_num_smokers()
    
    def _pause_simulation(self):
        """Pause the simulation."""
        self.is_running = False
        self.btn_start.setEnabled(True)
        self.btn_pause.setEnabled(False)
        self.timer.stop()
    
    def _reset_simulation(self):
        """Reset the simulation."""
        self._pause_simulation()
        
        self.simulation_time = 0.0
        self.smoke_sim.reset()
        self.fan.reset()
        self.data_logger.reset()
        self.fan_controller.reset_pid()
        
        for pair in self.sensor_pairs:
            pair.reset()
        
        self._update_displays()
        self.renderer_3d.update()
    
    def _update_num_smokers(self):
        """Update number of smokers."""
        num_smokers = self.spin_smokers.value()
        self.smoke_sim.set_num_smokers(num_smokers)
    
    def _update_simulation_speed(self):
        """Update simulation speed."""
        self.simulation_speed = self.spin_speed.value()
    
    def _change_fan_mode(self, mode_text):
        """Change fan mode.
        
        Args:
            mode_text: "Manual" or "Automatic"
        """
        mode = 'manual' if mode_text == "Manual" else 'auto'
        self.fan_controller.set_mode(mode)
        
        # Enable/disable manual controls
        self.manual_speed_group.setEnabled(mode == 'manual')
    
    def _manual_fan_speed_changed(self, value):
        """Handle manual fan speed change.
        
        Args:
            value: New speed value (0-100)
        """
        if self.fan_controller.mode == 'manual':
            self.fan.set_speed(value)
        self.label_fan_speed.setText(f"Fan Speed: {value}%")
    
    def _add_sensor_pair(self):
        """Add a new sensor pair."""
        if len(self.sensor_pairs) >= 4:
            QMessageBox.warning(self, "Maximum Sensors", "Maximum of 4 sensor pairs allowed.")
            return
        
        pair_id = len(self.sensor_pairs)
        distance = self.spin_sensor_distance.value()
        low_height = self.spin_low_height.value()
        high_height = self.spin_high_height.value()
        
        # Validate
        if low_height >= high_height:
            QMessageBox.warning(self, "Invalid Heights", "Low sensor must be below high sensor.")
            return
        
        # Create sensor pair
        sensor_pair = SensorPair(pair_id, distance, low_height, high_height, FAN_POSITION)
        self.sensor_pairs.append(sensor_pair)
        self.fan_controller.add_sensor_pair(sensor_pair)
        
        # Update list
        self.sensor_list.addItem(
            f"Pair {pair_id}: {distance}ft from fan, Low:{low_height}ft, High:{high_height}ft"
        )
        
        # Update renderer
        self.renderer_3d.sensor_pairs = self.sensor_pairs
        self.renderer_3d.update()
    
    def _remove_sensor_pair(self):
        """Remove selected sensor pair."""
        current_item = self.sensor_list.currentRow()
        if current_item >= 0:
            pair = self.sensor_pairs.pop(current_item)
            self.fan_controller.remove_sensor_pair(pair.pair_id)
            self.sensor_list.takeItem(current_item)
            
            # Update renderer
            self.renderer_3d.sensor_pairs = self.sensor_pairs
            self.renderer_3d.update()
    
    def _update_simulation(self):
        """Update simulation (called by timer)."""
        if not self.is_running:
            return
        
        # Time step
        dt = 0.033 * self.simulation_speed  # 33ms * speed multiplier
        
        # Update physics
        self.smoke_sim.update(dt)
        self.fan.update(dt)
        
        # Update sensors
        particles = self.smoke_sim.get_particles()
        for pair in self.sensor_pairs:
            pair.update(particles, dt)
        
        # Update controller
        self.fan_controller.update(dt)
        
        # Log data
        self.data_logger.update(self.simulation_time, self.fan, self.smoke_sim, self.sensor_pairs, dt)
        
        # Update time
        self.simulation_time += dt
        
        # Update 3D view
        self.renderer_3d.update()
    
    def _update_displays(self):
        """Update display panels (called by timer)."""
        # Update fan info
        fan_info = self.fan.get_info()
        info_text = f"""Current Speed: {fan_info['speed_percent']:.1f}%
Target Speed: {fan_info['target_speed']:.1f}%
CFM: {fan_info['cfm']:.0f}
Velocity: {fan_info['velocity']:.1f} ft/s
Run Time: {fan_info['run_time']:.1f} s
Status: {'Running' if fan_info['is_running'] else 'Off'}"""
        self.label_fan_info.setText(info_text)
        
        # Update sensor readings
        sensor_text = f"Simulation Time: {self.simulation_time:.1f}s\n\n"
        sensor_text += f"Room Average PPM: {self.smoke_sim.calculate_room_average_ppm():.1f}\n"
        sensor_text += f"Room Average Clarity: {self.smoke_sim.calculate_room_average_clarity():.1f}%\n"
        sensor_text += f"Active Particles: {self.smoke_sim.get_particle_count()}\n\n"
        
        for pair in self.sensor_pairs:
            readings = pair.get_readings()
            sensor_text += f"Sensor Pair {readings['pair_id']}:\n"
            sensor_text += f"  Low  - PPM: {readings['low']['ppm']:.1f}, Clarity: {readings['low']['clarity_percent']:.1f}%\n"
            sensor_text += f"  High - PPM: {readings['high']['ppm']:.1f}, Clarity: {readings['high']['clarity_percent']:.1f}%\n\n"
        
        self.text_sensor_data.setText(sensor_text)
        
        # Update graphs
        self._update_graphs()
        
        # Update statistics
        self._update_statistics()
    
    def _update_graphs(self):
        """Update real-time graphs."""
        graph_data = self.data_logger.get_graph_data()
        time_data = graph_data['time']
        
        if len(time_data) == 0:
            return
        
        # Clear and redraw PPM graph
        self.graph_ppm.clear()
        self.graph_ppm.plot(time_data, graph_data['room_ppm'], pen='w', name='Room Avg')
        
        colors = ['r', 'g', 'b', 'y']
        for idx, (sensor_id, ppm_data) in enumerate(graph_data['sensor_ppm'].items()):
            if len(ppm_data) > 0:
                color = colors[idx % len(colors)]
                self.graph_ppm.plot(time_data, ppm_data, pen=color, name=f'Sensor {sensor_id}')
        
        # Clear and redraw clarity graph
        self.graph_clarity.clear()
        self.graph_clarity.plot(time_data, graph_data['room_clarity'], pen='w', name='Room Avg')
        
        for idx, (sensor_id, clarity_data) in enumerate(graph_data['sensor_clarity'].items()):
            if len(clarity_data) > 0:
                color = colors[idx % len(colors)]
                self.graph_clarity.plot(time_data, clarity_data, pen=color, name=f'Sensor {sensor_id}')
        
        # Clear and redraw fan speed graph
        self.graph_fan.clear()
        self.graph_fan.plot(time_data, graph_data['fan_speed'], pen='c')
    
    def _update_statistics(self):
        """Update statistics display."""
        stats = self.data_logger.get_statistics()
        sim_stats = self.smoke_sim.get_statistics()
        
        stats_text = "=== SIMULATION STATISTICS ===\n\n"
        stats_text += f"Simulation Time: {sim_stats['time']:.1f} seconds\n\n"
        
        stats_text += "Air Quality:\n"
        stats_text += f"  Current Room PPM: {stats['current_room_ppm']:.1f}\n"
        stats_text += f"  Peak PPM: {stats['peak_ppm']:.1f}\n"
        stats_text += f"  Average PPM: {stats['average_ppm']:.1f}\n"
        stats_text += f"  Current Clarity: {stats['current_room_clarity']:.1f}%\n\n"
        
        if stats['time_to_clear'] is not None:
            stats_text += f"Time to Clear: {stats['time_to_clear']:.1f} seconds\n\n"
        else:
            stats_text += "Time to Clear: Not yet cleared\n\n"
        
        stats_text += "Particles:\n"
        stats_text += f"  Active Particles: {sim_stats['particle_count']}\n"
        stats_text += f"  Total Generated: {sim_stats['particles_generated']}\n"
        stats_text += f"  Total Removed: {sim_stats['particles_removed']}\n\n"
        
        stats_text += "Configuration:\n"
        stats_text += f"  Number of Smokers: {sim_stats['num_smokers']}\n"
        stats_text += f"  Sensor Pairs: {len(self.sensor_pairs)}\n"
        stats_text += f"  Fan Mode: {self.fan_controller.mode}\n"
        stats_text += f"  Simulation Speed: {self.simulation_speed}x\n\n"
        
        stats_text += f"Data Points Logged: {stats['data_points']}\n"
        
        self.text_statistics.setText(stats_text)
    
    def _save_configuration(self):
        """Save current configuration."""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Configuration", "configs", "JSON Files (*.json)"
        )
        
        if filename:
            config = ConfigManager.create_config_dict(
                self.sensor_pairs,
                self.spin_smokers.value(),
                self.fan_controller.mode,
                self.simulation_speed
            )
            
            self.config_manager.save_config(config, filename.split('/')[-1])
            QMessageBox.information(self, "Success", "Configuration saved successfully.")
    def _load_configuration(self):
        """Load a configuration."""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Load Configuration", "configs", "JSON Files (*.json)"
        )
        
        if filename:
            config = self.config_manager.load_config(filename.split('/')[-1])
            
            if config:
                # Reset first
                self._reset_simulation()
                
                # Clear existing sensors
                self.sensor_pairs.clear()
                self.fan_controller.clear_sensor_pairs()
                self.sensor_list.clear()
                
                # Load sensors
                for sensor_config in config.get('sensors', []):
                    pair_id = sensor_config['pair_id']
                    distance = sensor_config['distance_from_fan']
                    low_height = sensor_config['low_height']
                    high_height = sensor_config['high_height']
                    
                    sensor_pair = SensorPair(pair_id, distance, low_height, high_height, FAN_POSITION)
                    self.sensor_pairs.append(sensor_pair)
                    self.fan_controller.add_sensor_pair(sensor_pair)
                    
                    self.sensor_list.addItem(
                        f"Pair {pair_id}: {distance}ft from fan, Low:{low_height}ft, High:{high_height}ft"
                    )
                
                # Load simulation settings
                sim_config = config.get('simulation', {})
                self.spin_smokers.setValue(sim_config.get('num_smokers', DEFAULT_NUM_SMOKERS))
                self.spin_speed.setValue(sim_config.get('simulation_speed', DEFAULT_SIMULATION_SPEED))
                
                fan_mode = sim_config.get('fan_mode', 'manual')
                self.combo_fan_mode.setCurrentText('Automatic' if fan_mode == 'auto' else 'Manual')
                
                # Update renderer
                self.renderer_3d.sensor_pairs = self.sensor_pairs
                self.renderer_3d.update()
                
                QMessageBox.information(self, "Success", "Configuration loaded successfully.")
            else:
                QMessageBox.warning(self, "Error", "Could not load configuration file.")
    
    def _export_data(self):
        """Export data to CSV."""
        filepath = self.data_logger.export_to_csv()
        
        if filepath:
            QMessageBox.information(
                self, "Success", 
                f"Data exported successfully to:\n{filepath}"
            )
        else:
            QMessageBox.warning(self, "Error", "No data to export.")