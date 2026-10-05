#!/bin/bash

echo "Creating virtual environment..."
python3 -m venv venv

echo "Activating virtual environment..."
source venv/bin/activate

echo "Upgrading pip..."
pip install --upgrade pip

echo "Installing requirements..."
pip install -r requirements.txt

echo "Initializing database..."
python3 backend/seed.py

echo "Setup complete! Remember to run 'source venv/bin/activate' before starting your app."