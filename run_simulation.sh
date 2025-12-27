#!/bin/bash
# Quick start script for Cigar Lounge Smoke Simulation Tool

echo "Starting Cigar Lounge Smoke Simulation Tool..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    echo "Installing dependencies..."
    pip install -q -r requirements.txt
else
    source venv/bin/activate
fi

# Run the application
python3 main.py
