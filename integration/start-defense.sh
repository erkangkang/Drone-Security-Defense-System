#!/bin/bash
set -e

echo "=========================================="
echo " Drone Security Defense System - Docker"
echo "=========================================="

# Set Python path
export PYTHONPATH="/app/src:${PYTHONPATH}"

# Wait for companion computer network to be ready
echo "Waiting for companion computer (10.13.0.3)..."
for i in $(seq 1 30); do
    if ping -c 1 -W 1 10.13.0.3 > /dev/null 2>&1; then
        echo "Companion computer is reachable."
        break
    fi
    if [ "$i" -eq 30 ]; then
        echo "WARNING: Companion computer not reachable after 60s, starting anyway..."
    fi
    sleep 2
done

echo "Starting defense system..."
exec python3 -m src.main --config /app/config/docker_config.yaml --log-level INFO
