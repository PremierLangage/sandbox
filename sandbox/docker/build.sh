#!/usr/bin/env bash
docker ps -a | awk '{ print $1,$2 }' | grep pl:latest | awk '{print $1 }' | xargs -I {} docker stop {} > /dev/null
docker rmi -f pl:latest || true
docker build -t pl:latest .
systemctl restart docker
