#!/bin/bash

# EduBot Server Activator Script for Linux/Mac

echo "========================================"
echo "    EDUBOT SERVER ACTIVATOR"
echo "========================================"
echo ""
echo "Starting EduBot Server and Telegram Bot..."
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "ERROR: Python not found!"
        echo "Please install Python 3.7 or higher"
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

# Check if required files exist
if [ ! -f "ngrok" ]; then
    echo "ERROR: ngrok not found!"
    echo "Please download ngrok from: https://ngrok.com/download"
    exit 1
fi

if [ ! -f "wsgi.py" ]; then
    echo "ERROR: wsgi.py not found!"
    echo "Please ensure you're in the correct directory"
    exit 1
fi

# Make ngrok executable
chmod +x ngrok

echo ""
echo "✅ Requirements checked!"
echo "🚀 Starting activation..."
echo ""

# Run the activation script
$PYTHON_CMD activate_server.py

echo ""
echo "========================================"
echo "    ACTIVATION COMPLETED"
echo "========================================"
echo ""
echo "Thank you for using EduBot!"
echo ""
