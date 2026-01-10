## Immich AutoTag Docker Usage Guide

### 1. Build the image locally

```bash
./scripts/build_docker_image.sh
```

### 2. Run with your configuration

Mount your config directory so the container can read it:

```bash
docker run --rm \
  -v $HOME/.config/immich_autotag:/home/autotaguser/.config/immich_autotag \
  immich-autotag:latest
```

### 3. Accessing logs

- By default, logs are printed to the container's stdout/stderr. You can see them directly in your terminal or with `docker logs <container_id>` if running detached.
- If you want to persist log files, mount the logs directory as a volume:

```bash
docker run --rm \
  -v $HOME/.config/immich_autotag:/home/autotaguser/.config/immich_autotag \
  -v $PWD/logs:/home/autotaguser/logs \
  immich-autotag:latest
```

### 4. Periodic execution (cron example)

Add a cron job on your host to run the container periodically. Example (every day at 2am):

```cron
0 2 * * * docker run --rm -v $HOME/.config/immich_autotag:/home/autotaguser/.config/immich_autotag immich-autotag:latest
```

---

For advanced usage, override the default command or entrypoint as needed. See the main README for more details.