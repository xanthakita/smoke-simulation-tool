# Installation Guide

## Quick Start (Linux/Mac)

```bash
# Make the run script executable
chmod +x run_simulation.sh

# Run the application
./run_simulation.sh
```

The script will automatically:
1. Create a virtual environment (if needed)
2. Install all dependencies
3. Launch the application

## Manual Installation

### Prerequisites

- **Python 3.8 or higher**
- **pip** (Python package manager)
- **OpenGL support** (usually built into most systems)

### Step-by-Step Installation

#### 1. Verify Python Installation

```bash
python3 --version
```

Should show Python 3.8 or higher.

#### 2. Create Virtual Environment (Recommended)

```bash
cd smoke_simulation_tool
python3 -m venv venv
```

#### 3. Activate Virtual Environment

**Linux/Mac:**
```bash
source venv/bin/activate
```

**Windows:**
```bash
venv\Scripts\activate
```

#### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- PyQt5 (GUI framework)
- PyOpenGL (3D graphics)
- NumPy (numerical computing)
- SciPy (scientific computing)
- Matplotlib (plotting)
- Pandas (data analysis)
- PyQtGraph (real-time plotting)

#### 5. Run the Application

```bash
python main.py
```

## Troubleshooting

### OpenGL Issues

If you encounter OpenGL-related errors:

**Linux:**
```bash
sudo apt-get update
sudo apt-get install python3-opengl
```

**Mac:**
OpenGL should be pre-installed. If issues persist:
```bash
brew install freeglut
```

**Windows:**
Download and install the latest graphics drivers for your GPU.

### PyQt5 Issues

If PyQt5 doesn't install properly:

**Linux:**
```bash
sudo apt-get install python3-pyqt5 python3-pyqt5.qtopengl
```

**Mac:**
```bash
brew install pyqt5
```

**Windows:**
Try installing from a wheel file:
```bash
pip install PyQt5-sip
pip install PyQt5
```

### Import Errors

If you get import errors when running:

1. Ensure you're in the correct directory:
   ```bash
   cd smoke_simulation_tool
   ```

2. Verify virtual environment is activated:
   ```bash
   which python  # Should show path to venv
   ```

3. Reinstall dependencies:
   ```bash
   pip install --force-reinstall -r requirements.txt
   ```

### Performance Issues

If the simulation runs slowly:

1. **Install Numba** (optional, for faster physics):
   ```bash
   pip install numba
   ```

2. **Reduce particle count**: Lower the number of smokers in the simulation

3. **Update graphics drivers**: Ensure you have the latest GPU drivers

4. **Use a dedicated GPU**: If available, configure your system to use the dedicated GPU for the application

## System Requirements

### Minimum Requirements
- **CPU**: Dual-core processor, 2 GHz or faster
- **RAM**: 4 GB
- **Graphics**: OpenGL 2.1 compatible
- **OS**: 
  - Linux (Ubuntu 18.04+ or equivalent)
  - macOS 10.13+
  - Windows 10+
- **Disk Space**: 500 MB

### Recommended Requirements
- **CPU**: Quad-core processor, 3 GHz or faster
- **RAM**: 8 GB or more
- **Graphics**: Dedicated GPU with OpenGL 3.0+
- **OS**: Latest stable version
- **Disk Space**: 1 GB

## Uninstallation

To remove the application:

1. **Delete the virtual environment:**
   ```bash
   rm -rf venv
   ```

2. **Delete the entire project directory:**
   ```bash
   cd ..
   rm -rf smoke_simulation_tool
   ```

## Getting Help

If you continue to experience issues:

1. Check the **USER_GUIDE.md** for usage instructions
2. Review the **README.md** for project overview
3. Examine log files in the application directory
4. Ensure all prerequisites are met

## Verification

To verify the installation is correct:

```bash
python3 -c "from gui.main_window import MainWindow; print('Installation successful!')"
```

If you see "Installation successful!", everything is set up correctly.
