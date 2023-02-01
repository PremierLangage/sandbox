#!/bin/bash

# COLORS
# Reset
Color_Off=$'\e[0m' # Text Reset

# Regular Colors
Red=$'\e[0;31m'    # Red
Green=$'\e[0;32m'  # Green
Yellow=$'\e[0;33m' # Yellow
Purple=$'\e[0;35m' # Purple
Cyan=$'\e[0;36m'   # Cyan

# Building container
echo "$Yellow"
echo "Creating container image...$Color_Off"
docker ps -a | awk '{ print $1,$2 }' | grep pl:latest | awk '{print $1 }' | xargs -I {} docker stop {} > /dev/null
docker rmi -f pl:latest &> /dev/null || true
docker build -t pl:latest docker/ || {
    echo -n "$Red" >&2
    echo "ERROR: 'docker build -t pl:latest docker/' failed." >&2
    echo "If getting: 'container: Error response from daemon: grpc: the connection is unavailable.'" >&2
    echo "try: systemctl restart docker$Color_Off" >&2
    exit 1
}

echo "$Green"
echo "Image built successfully !$Color_Off"
