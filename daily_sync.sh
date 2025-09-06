#!/bin/bash
# Linux/Mac shell script for St. Louis 311+ daily sync
# Run this script daily via cron job

echo "Starting St. Louis 311+ Daily Sync at $(date)"

# Navigate to project directory (update this path as needed)
cd /path/to/stl311_plus

# Check if containers are running, start them if needed
echo "Checking Docker container status..."
if ! docker-compose ps | grep -q "stl311_flask"; then
    echo "Docker containers not running. Starting them..."
    docker-compose up -d
    echo "Waiting for containers to be ready..."
    sleep 30
    echo "Containers started."
else
    echo "Docker containers are already running."
fi

# Run daily sync using Docker
echo "Running daily sync..."
docker exec stl311_flask python daily_sync.py yesterday

if [ $? -eq 0 ]; then
    echo "Daily sync completed successfully at $(date)"
else
    echo "Daily sync failed at $(date)"
fi

echo "Sync operation finished"
