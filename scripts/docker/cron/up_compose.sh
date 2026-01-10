#!/bin/bash
# Script to start the autotag-cron service with Docker Compose

set -e

cd "$(dirname "$0")/../.."

docker compose up -d

echo "autotag-cron service started with Docker Compose."
