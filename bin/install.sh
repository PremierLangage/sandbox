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


# Checking if python >= 3.7 is installed
if ! hash python3; then
    echo "Python3:$Red ERROR - Python 3.7 (or a more recent version) must be installed (see: https://www.python.org/).$Color_Off" >&2
    exit 1
fi

ver=$(python3 --version 2>&1 | sed 's/.* \([0-9]\).\([0-9]\).*/\1\2/')
if [[ "$ver" -lt "37" ]]; then
    echo "python3:$Red ERROR - $(python3 -V | tr -d '\n') found, should be at least 3.7 (see: https://www.python.org/).$Color_Off" >&2
    exit 1
fi
echo "python3:$Green OK !$Color_Off"

# Checking if Docker is installed
if ! hash docker 2> /dev/null; then
    echo "docker:$Red ERROR - Docker must be installed (see: https://docs.docker.com/engine/installation/linux/docker-ce/debian/).$Color_Off" >&2
    exit 1
fi
echo "docker:$Green OK !$Color_Off"

# Checking if pip3 is installed
if ! hash pip3; then
    echo "pip3:$Red ERROR - Pip3 must be installed (see: https://pip.pypa.io/en/stable/installing/)." >&2
    exit 1
fi
echo "pip3:$Green OK !$Color_Off"

# Getting requirement
echo "$Yellow"
echo "Installing requirements... $Color_Off"
pip3 install wheel || {
    echo -n "$Red" >&2
    echo "ERROR: 'pip3 install wheel' failed.$Color_Off" >&2
    exit 1
}
pip3 install -r requirements.txt || {
    echo -n "$Red" >&2
    echo "ERROR: 'pip3 install -r requirements.txt' failed.$Color_Off" >&2
    exit 1
}
echo -n "$Green"
echo "Done !$Color_Off"

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
echo "Installation successfull !$Color_Off"
echo "You can try to run the server with$Purple python3 manage.py runserver [port]$Color_Off"
