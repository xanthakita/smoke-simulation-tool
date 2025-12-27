#!/usr/bin/env python3
"""Main entry point for the Cigar Lounge Smoke Simulation Tool."""

import sys
from PyQt5.QtWidgets import QApplication
from gui.main_window import MainWindow


def main():
    """Main function to start the application."""
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("Cigar Lounge Smoke Simulation")
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Start event loop
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
