#!/bin/bash
echo "Starting DataLens Backend Server..."
echo "Server will be available at: http://0.0.0.0:8080"
echo "Press Ctrl+C to stop the server"
echo

python manage.py runserver 0.0.0.0:8080
