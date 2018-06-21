docker ps -a | awk '{ print $1,$2 }' | grep pl:base | awk '{print $1 }' | xargs -I {} docker stop {} > /dev/null
docker rmi -f pl:base || true
docker build -t pl:base .
systemctl restart docker
