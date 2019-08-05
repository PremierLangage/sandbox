#!/usr/bin/env bash
#Checking if python >= 3.7 is installed
if ! hash python3; then
    echo "ERROR: Python >= 3.7 should be installed."
    exit 1
fi

ver=$(python3 --version 2>&1 | sed 's/.* \([0-9]\).\([0-9]\).*/\1\2/')
if [[ "$ver" -lt "37" ]]; then
    echo "ERROR: Python >= 3.7 should be installed."
    exit 1
fi
echo "Python >= 3.7: OK !"

#Checking if Docker is installed
command -v docker >/dev/null 2>&1 || { echo >&2 "ERROR: Docker should be installed (see: https://docs.docker.com/engine/installation/linux/docker-ce/debian/)."; exit 1; }
echo "docker: OK !"

#Checking if pip3 is installed
command -v pip3 >/dev/null 2>&1 || { echo >&2 "ERROR: pip3 should be installed"; exit 1; }
echo "pip3: OK !"

#Getting requirement
echo ""
echo "Installing requirements..."
pip3 install wheel || { echo>&2 "ERROR: pip3 install wheel failed" ; exit 1; }
pip3 install -r requirements.txt || { echo>&2 "ERROR: pip3 install -r requirements.txt failed" ; exit 1; }
echo "Done !"

#Building container
echo ""
echo "Creating container image..."
cd docker/
./build.sh || { cd -; echo>&2 "ERROR: docker/build.sh failed" ; echo "if getting: 'container: Error response from daemon: grpc: the connection is unavailable.'"; echo "try: systemctl restart docker" ; exit 1; }
echo "Done !"
