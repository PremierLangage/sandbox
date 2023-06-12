#!/bin/bash

# echo "Creating database..."
docker run --name activities-db \
    -e POSTGRES_USER=activity_user \
    -e POSTGRES_PASSWORD=Dimz80k7X97! \
    -e POSTGRES_DB=activity_db \
    -v /mnt/data/activities_data:/var/lib/postgresql/data postgres \
    --restart unless-stopped \
    -d

while true; do
    echo -n "Please enter the number of sandbox containers: "
    read -r DOCKER_COUNT
    if [[ "$DOCKER_COUNT" =~ ^[0-9]+$ ]]; then
        echo "Connecting the containers to the database..."
        break
    else
        echo "error: Not a number"
    fi
done

# echo "Creating networks..."
i=0
while [ $i -lt $DOCKER_COUNT ]; do
    docker network create --internal c$i
    i=$(($i + 1))
done

# echo "Connecting containers to the database..."
i=0
while [ $i -lt $DOCKER_COUNT ]; do
    docker network connect c$i activities-db
    i=$(($i + 1))
done
