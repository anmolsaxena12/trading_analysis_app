#!/bin/bash

# Trading Analysis App Startup Script

echo "🚀 Starting Trading Analysis App..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/upgrade requirements
echo "📥 Installing requirements..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cp .env.template .env
    echo "📝 Please edit .env file with your API credentials before running the app."
    exit 1
fi

# Start the application
echo "🌟 Starting the application..."
echo "📱 Access the app at: http://localhost:5000"
python app.py