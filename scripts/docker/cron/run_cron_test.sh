#!/bin/bash
# Run the cron-enabled Immich AutoTag container locally for testing
set -e

# Default: run every minute for quick testing
CRON_SCHEDULE="${CRON_SCHEDULE:-* * * * *}"

# Use config from host
CONFIG_DIR="$HOME/.config/immich_autotag"

# Remove any previous test container
if docker ps -a --format '{{.Names}}' | grep -Eq '^autotag-cron-test$'; then
	docker rm -f autotag-cron-test
fi

docker run -d --name autotag-cron-test \
	-e CRON_SCHEDULE="$CRON_SCHEDULE" \
	-v "$CONFIG_DIR:/root/.config/immich_autotag" \
	txemi/immich-autotag:cron

echo "Container 'autotag-cron-test' started."
echo "To see logs: docker exec -it autotag-cron-test tail -f /var/log/cron.log"
