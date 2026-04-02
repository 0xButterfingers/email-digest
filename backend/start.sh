#!/bin/bash

# Email Digest Summarizer - Backend Startup Script

set -e

echo "Starting Email Digest Summarizer Backend..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "Please configure .env with your credentials and run this script again."
    exit 1
fi

# Start the application
echo "Starting FastAPI server..."
uvicorn main:app --reload --host 0.0.0.0 --port 8000
