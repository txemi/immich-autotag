#!/bin/bash
set -e

# Uses CRON_SCHEDULE or default value (every day at 2:00 AM)
CRON_SCHEDULE="${CRON_SCHEDULE:-0 2 * * *}"

# Generates the crontab from the template
sed "s|{{CRON_SCHEDULE}}|$CRON_SCHEDULE|g" /crontab.template > /etc/cron.d/immich_autotag
chmod 0644 /etc/cron.d/immich_autotag
crontab /etc/cron.d/immich_autotag

# Starts cron in foreground
cron -f
