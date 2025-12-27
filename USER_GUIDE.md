# User Guide - Cigar Lounge Smoke Simulation Tool

## Table of Contents
1. [Getting Started](#getting-started)
2. [User Interface Overview](#user-interface-overview)
3. [Running a Simulation](#running-a-simulation)
4. [Configuring Sensors](#configuring-sensors)
5. [Fan Control](#fan-control)
6. [Interpreting Results](#interpreting-results)
7. [Advanced Features](#advanced-features)

---

## Getting Started

### Installation

1. **Install Python 3.8+** (if not already installed)
   ```bash
   python3 --version  # Check your Python version
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Application**
   ```bash
   python main.py
   ```

### First Time Setup

When you first launch the application:
1. You'll see a 3D view of the empty room on the left
2. Control panels are below the 3D view
3. Data displays and graphs are on the right side

---

## User Interface Overview

### Main Window Layout

The application window is divided into two main sections:

#### Left Panel: 3D View and Controls
- **3D Visualization**: Shows the room, smoke particles, sensors, and fan
  - Use mouse to rotate view (click and drag)
  - Use mouse wheel to zoom in/out
- **Control Tabs**:
  - **Simulation Tab**: Start/pause/reset, smoker count, simulation speed
  - **Sensors Tab**: Add/remove sensor pairs and configure positions
  - **Fan Control Tab**: Switch between manual/auto mode, set fan speed

#### Right Panel: Data and Analysis
- **Data Tabs**:
  - **Sensor Readings**: Real-time PPM and clarity values for all sensors
  - **Graphs**: Time-series plots of PPM, clarity, and fan speed
  - **Statistics**: Summary statistics and export options

---

## Running a Simulation

### Basic Workflow

#### Step 1: Set Number of Smokers
1. Go to **Simulation** tab (bottom left)
2. Adjust "Number of Smokers" spinner (0-48)
3. Default is 24 smokers

#### Step 2: Add Sensor Pairs (Optional but Recommended)
1. Go to **Sensors** tab
2. Set sensor configuration:
   - **Distance from Fan**: How far from the fan (in feet)
   - **Low Sensor Height**: Height of low sensor from floor
   - **High Sensor Height**: Height of high sensor from floor
3. Click "Add Sensor Pair"
4. Repeat to add up to 4 pairs

**Recommended Sensor Configurations:**
- **Near-Fan Pair**: 10ft from fan, Low:3ft, High:12ft
- **Mid-Room Pair**: 35ft from fan, Low:3ft, High:12ft
- **Far Pair**: 60ft from fan, Low:3ft, High:12ft

#### Step 3: Configure Fan Control
1. Go to **Fan Control** tab
2. Choose mode:
   - **Manual**: You control fan speed with slider
   - **Automatic**: Controller adjusts speed based on sensor readings
3. For Manual mode: Use slider to set desired fan speed (0-100%)

#### Step 4: Start Simulation
1. Click **Start** button in Simulation tab
2. Watch the 3D view as smoke particles are generated and move
3. Monitor sensor readings in real-time on the right panel
4. Observe graphs updating automatically

#### Step 5: Analyze Results
1. Switch to **Statistics** tab to see summary
2. Look for:
   - Peak PPM values
   - Time to clear the room
   - Average air quality
3. Export data to CSV for detailed analysis

---

## Configuring Sensors

### Sensor Pair Concept

Each sensor pair consists of:
- **Low Sensor** (Green): Placed at breathing level (~3ft)
- **High Sensor** (Red): Placed near ceiling where smoke accumulates (~12ft)

### Placement Guidelines

#### Distance from Fan
- **Close (5-15ft)**: Detects smoke being drawn to fan
- **Medium (20-40ft)**: Monitors mid-room conditions
- **Far (45-65ft)**: Checks front of room (farthest from fan)

#### Height Guidelines
- **Low Sensor**: 2-4 feet (breathing/sitting level)
- **High Sensor**: 10-16 feet (smoke accumulation zone)
- **Minimum separation**: 2 feet between low and high

### Strategic Placement Examples

#### Configuration 1: Single Pair (Minimum)
- **Pair 1**: 30ft from fan, Low:3ft, High:12ft
  - General room monitoring

#### Configuration 2: Three Pairs (Recommended)
- **Pair 1**: 15ft from fan, Low:3ft, High:12ft (Near fan)
- **Pair 2**: 35ft from fan, Low:3ft, High:12ft (Middle)
- **Pair 3**: 60ft from fan, Low:3ft, High:12ft (Far end)
  - Provides comprehensive coverage

#### Configuration 3: Four Pairs (Maximum Coverage)
- **Pair 1**: 10ft from fan, Low:3ft, High:15ft
- **Pair 2**: 25ft from fan, Low:3ft, High:12ft
- **Pair 3**: 45ft from fan, Low:3ft, High:12ft
- **Pair 4**: 65ft from fan, Low:3ft, High:10ft
  - Maximum spatial resolution

---

## Fan Control

### Manual Mode

In manual mode, you have direct control:
1. Select "Manual" from Fan Mode dropdown
2. Use the slider to set fan speed (0-100%)
3. Fan will ramp to target speed gradually
4. Monitor CFM and velocity in Fan Information panel

**Use Cases for Manual Mode:**
- Testing specific fan speeds
- Demonstrating fan effectiveness
- Baseline comparisons
- When you want consistent, predictable behavior

### Automatic Mode

In automatic mode, the controller manages fan speed:
1. Select "Automatic" from Fan Mode dropdown
2. Controller monitors all sensor pairs
3. Adjusts fan speed based on smoke levels
4. Uses PID control for smooth response

**How Automatic Control Works:**

1. **Low Sensors** determine if air quality is acceptable
   - Below threshold → Consider turning off fan
   - Above threshold → Keep fan running

2. **High Sensors** determine required fan power
   - Higher smoke concentration → Higher fan speed
   - Uses worst-case sensor reading

3. **Control Logic:**
   ```
   PPM < 50:        20% fan speed (minimum)
   PPM 50-150:      40% fan speed (moderate)
   PPM 150-300:     70% fan speed (high)
   PPM > 300:       100% fan speed (maximum)
   ```

4. **Safety Features:**
   - Minimum run time of 30 seconds
   - Gradual ramp up/down
   - Won't turn off if low sensors detect smoke

---

## Interpreting Results

### Key Metrics

#### PPM (Parts Per Million)
Indicates particle concentration in air:
- **0-50**: Clean/Good air quality
- **50-150**: Moderate (noticeable but acceptable)
- **150-300**: Unhealthy (uncomfortable)
- **300+**: Very unhealthy (poor visibility)

#### Air Clarity (%)
Indicates visual transmission:
- **100%**: Perfect visibility
- **85-100%**: Slight haze
- **60-85%**: Noticeable haze
- **40-60%**: Heavy smoke
- **<40%**: Very dense smoke

### Understanding the Graphs

#### PPM Over Time Graph
- Shows particle concentration trends
- Multiple lines represent different sensors
- Room average shown in white
- **What to look for:**
  - Rate of PPM increase (with smokers active)
  - Rate of PPM decrease (when fan is on)
  - Differences between sensor locations

#### Clarity Over Time Graph
- Mirrors PPM but from visibility perspective
- Higher is better
- **What to look for:**
  - How quickly visibility degrades
  - How quickly fan restores visibility
  - Which areas clear first

#### Fan Speed Over Time Graph
- Shows fan controller behavior
- In auto mode, shows how controller responds
- **What to look for:**
  - Response time to smoke detection
  - Speed variations during clearing
  - Patterns in control strategy

### Statistics Panel

Key statistics to review:

- **Peak PPM**: Highest concentration reached
  - Lower is better
  - Indicates worst-case scenario

- **Average PPM**: Overall air quality
  - Indicates typical conditions
  - Useful for comparing configurations

- **Time to Clear**: Seconds to reach clean air
  - Critical metric for fan sizing
  - Lower is better

- **Current Values**: Real-time conditions
  - Monitor during simulation

### Comparing Configurations

To optimize your setup:

1. **Run baseline**: Default configuration
2. **Change one variable**: 
   - Number of smokers
   - Sensor locations
   - Fan control strategy
3. **Compare statistics**:
   - Time to clear
   - Peak PPM
   - Average PPM
4. **Export data** for detailed analysis

---

## Advanced Features

### Simulation Speed Control

Adjust how fast the simulation runs:
- **1.0x**: Real-time (1 second = 1 second)
- **2.0x**: Double speed
- **5.0x**: Five times faster
- **0.5x**: Half speed (for detailed observation)

**Use Cases:**
- Fast speed: Quick testing of long-term scenarios
- Slow speed: Detailed observation of smoke behavior
- Real-time: Accurate timing measurements

### Configuration Management

#### Saving Configurations
1. Set up sensors and simulation parameters
2. Click "Save Configuration" in Simulation tab
3. Choose filename and location
4. Configuration saved as JSON file

**Saved Settings Include:**
- All sensor pair locations
- Number of smokers
- Fan control mode
- Simulation speed

#### Loading Configurations
1. Click "Load Configuration"
2. Select saved JSON file
3. System resets and applies saved configuration
4. Ready to run simulation

**Use Cases:**
- Save different scenarios for testing
- Share configurations with colleagues
- Return to previous tests
- Document optimization process

### Data Export

#### CSV Export
1. Run a simulation
2. Go to Statistics tab
3. Click "Export Data to CSV"
4. File saved to `exports/` directory

**CSV Contains:**
- Timestamp for each data point
- Fan speed at each moment
- Room average PPM and clarity
- Individual sensor readings (PPM and clarity)
- Particle count

**Analysis Options:**
- Import into Excel or Google Sheets
- Use Python/R for statistical analysis
- Create custom visualizations
- Generate reports

### 3D View Controls

#### Navigation
- **Rotate**: Click and drag with left mouse button
- **Zoom**: Scroll mouse wheel
- **Pan**: (currently not implemented)

#### View Options
Visible elements (currently always on):
- Room boundaries with floor grid
- Smoke particles (gray points)
- Sensors (green=low, red=high)
- Exhaust fan (blue circle)

**Tips for Better Viewing:**
- Rotate to see smoke flow toward fan
- Zoom in to see sensor details
- Zoom out for overall room view
- Side view shows stratification clearly

### Keyboard Shortcuts

(Note: These require focus on specific widgets)

- **Space**: Start/Pause (when focused on button)
- **+/-**: Adjust values in spinboxes
- **Tab**: Navigate between controls
- **Enter**: Activate focused button

---

## Tips and Best Practices

### Getting Meaningful Results

1. **Start Simple**
   - Begin with 1 sensor pair
   - Use medium number of smokers (24)
   - Run in real-time (1x speed)

2. **Add Complexity Gradually**
   - Add more sensor pairs
   - Try different locations
   - Experiment with fan modes

3. **Test Systematically**
   - Change one variable at a time
   - Keep notes on configurations
   - Save configurations before changing

4. **Use Statistics**
   - Focus on "Time to Clear" metric
   - Compare peak PPM values
   - Look at sensor-to-sensor differences

### Common Scenarios

#### Scenario 1: Initial Assessment
**Goal**: Understand current room performance
- Use 48 smokers (full capacity)
- Place 2-3 sensor pairs
- Run in auto mode
- Export results as baseline

#### Scenario 2: Optimize Fan Control
**Goal**: Find best automatic control strategy
- Fixed smoker count (24)
- Multiple sensor locations
- Compare auto vs manual at different speeds
- Measure time to clear

#### Scenario 3: Sensor Placement Study
**Goal**: Find best sensor locations
- Fixed fan speed (manual mode)
- Test different sensor positions
- Compare detection times
- Find earliest warning positions

### Troubleshooting

#### Simulation Runs Slowly
- Reduce number of smokers
- Lower simulation speed
- Close other applications

#### Particles Not Visible
- Zoom in to room
- Wait for particles to generate
- Check that simulation is running

#### Fan Not Responding
- Check if in Manual mode
- Verify slider is not at 0%
- In Auto mode, check if sensors detect smoke

#### Sensors Show No Readings
- Ensure simulation is running
- Wait for smoke to reach sensors
- Check sensor placement (inside room?)

---

## Appendix: Technical Details

### Physics Model Summary

The simulation uses particle-based computational fluid dynamics:

1. **Particle Generation**: 500 particles/cigar/second
2. **Forces Applied**:
   - Buoyancy (upward, temperature-based)
   - Diffusion (random dispersion)
   - Advection (fan suction)
   - Gravity (cooling particles)
3. **Boundary Conditions**: Elastic collisions with walls
4. **Removal**: Particles removed at fan or after 5 minutes

### Accuracy and Limitations

**What the Simulation Does Well:**
- General smoke movement patterns
- Relative comparisons between configurations
- Fan effectiveness demonstration
- Sensor placement optimization

**Limitations:**
- Simplified turbulence model
- No HVAC inlet modeling (yet)
- Uniform particle size
- Ideal mixing assumptions
- No temperature gradients (except buoyancy)

**For Production Use:**
- Use as design tool, not final specification
- Validate with real-world measurements
- Consider CFD analysis for critical applications
- Factor in safety margins

---

## Support and Feedback

For questions, issues, or suggestions:
- Review README.md for technical details
- Check this guide for usage questions
- Examine example configurations in `configs/` directory

---

**Version**: 1.0  
**Last Updated**: December 2025
