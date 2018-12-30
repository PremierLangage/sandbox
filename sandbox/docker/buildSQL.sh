
#!/usr/bin/env bash
docker ps -a | awk '{ print $1,$2 }' | grep pl:base | awk '{print $1 }' | xargs -I {} docker stop {} > /dev/null
docker rmi -f pl:base || true
docker build -file DockerfileSQL -t pl:sql .
systemctl restart docker
