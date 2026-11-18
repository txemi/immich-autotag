#!/bin/bash
set -e

# Uses CRON_SCHEDULE or default value (every day at 2:00 AM)
CRON_SCHEDULE="${CRON_SCHEDULE:-0 2 * * *}"

# Generates the crontab from the template
# cron starts jobs without the container's environment: carry the dry-run switch into the
# crontab, so `docker run -e IMMICH_AUTOTAG_DRY_RUN=1` really is a dry run (empty = normal run).
# The application validates the value and stops on anything it does not know.
{
  if [ -n "${IMMICH_AUTOTAG_DRY_RUN:-}" ]; then
    printf 'IMMICH_AUTOTAG_DRY_RUN=%s\n' "$IMMICH_AUTOTAG_DRY_RUN"
  fi
  sed "s|{{CRON_SCHEDULE}}|$CRON_SCHEDULE|g" /crontab.template
} > /etc/cron.d/immich_autotag
chmod 0644 /etc/cron.d/immich_autotag
crontab /etc/cron.d/immich_autotag

# Starts cron in foreground
cron -f
