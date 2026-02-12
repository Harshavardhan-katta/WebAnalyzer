#!/bin/bash
# Startup script for Railway
cd backend
echo "Checking dependencies..."
python -c "import flask; import flask_cors; import requests; import bs4; import reportlab; import matplotlib; from PIL import Image; print('✓ All imports successful')" || exit 1
echo "Starting gunicorn..."
gunicorn -w 1 -b 0.0.0.0:$PORT --timeout 120 --access-logfile - app:app
