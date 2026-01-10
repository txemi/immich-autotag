#!/bin/bash
set -e

# Usa CRON_SCHEDULE o valor por defecto (cada día a las 2:00)
CRON_SCHEDULE="${CRON_SCHEDULE:-0 2 * * *}"

# Genera el crontab a partir de la plantilla
sed "s|{{CRON_SCHEDULE}}|$CRON_SCHEDULE|g" /crontab.template > /etc/cron.d/immich_autotag
chmod 0644 /etc/cron.d/immich_autotag
crontab /etc/cron.d/immich_autotag

# Arranca cron en primer plano
cron -f
