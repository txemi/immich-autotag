#!/bin/bash
# Push the cron-enabled Docker image to Docker Hub
set -e
docker push txemi/immich-autotag:cron
echo "\nPushed image: txemi/immich-autotag:cron"
