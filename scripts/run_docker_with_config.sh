
#!/bin/bash
# Script portable para arrancar el contenedor Docker de immich-autotag montando config
# Uso: bash scripts/run_docker_with_config.sh <ruta_local_config> [opciones_docker]


IMAGE_NAME="immich-autotag:latest"
CONTAINER_CONFIG_DIR="/home/immich_autotag/.config/immich_autotag"

# Si se pasa argumento, usarlo como ruta de config
if [ -n "$1" ]; then
  CONFIG_LOCAL_PATH="$1"
  shift
else
  # Buscar automáticamente en las rutas típicas
  # 1. Desarrollo: user_config.py/yaml en ./immich_autotag/config/
  if [ -f "immich_autotag/config/user_config.py" ]; then
    CONFIG_LOCAL_PATH="immich_autotag/config/user_config.py"
  elif [ -f "immich_autotag/config/user_config.yaml" ]; then
    CONFIG_LOCAL_PATH="immich_autotag/config/user_config.yaml"
  # 2. Home config: ~/.config/immich_autotag/config.py/yaml
  elif [ -f "$HOME/.config/immich_autotag/config.py" ]; then
    CONFIG_LOCAL_PATH="$HOME/.config/immich_autotag/config.py"
  elif [ -f "$HOME/.config/immich_autotag/config.yaml" ]; then
    CONFIG_LOCAL_PATH="$HOME/.config/immich_autotag/config.yaml"
  # 3. Legacy: ~/.immich_autotag/config.py/yaml
  elif [ -f "$HOME/.immich_autotag/config.py" ]; then
    CONFIG_LOCAL_PATH="$HOME/.immich_autotag/config.py"
  elif [ -f "$HOME/.immich_autotag/config.yaml" ]; then
    CONFIG_LOCAL_PATH="$HOME/.immich_autotag/config.yaml"
  # 4. Directorio completo (desarrollo)
  elif [ -d "immich_autotag/config" ]; then
    CONFIG_LOCAL_PATH="immich_autotag/config"
  # 5. Directorio completo (home)
  elif [ -d "$HOME/.config/immich_autotag" ]; then
    CONFIG_LOCAL_PATH="$HOME/.config/immich_autotag"
  elif [ -d "$HOME/.immich_autotag" ]; then
    CONFIG_LOCAL_PATH="$HOME/.immich_autotag"
  else
    echo "ERROR: No se encontró configuración en rutas típicas."
    echo "Puedes pasar la ruta como argumento: $0 <ruta_local_config> [opciones_docker]"
    exit 1
  fi
fi


# Convertir ruta a absoluta
CONFIG_ABS_PATH="$(realpath "$CONFIG_LOCAL_PATH")"

if [ -d "$CONFIG_ABS_PATH" ]; then
  # Montar directorio completo
  echo "Montando directorio de configuración: $CONFIG_ABS_PATH -> $CONTAINER_CONFIG_DIR"
  docker run --rm \
    -v "$CONFIG_ABS_PATH":"$CONTAINER_CONFIG_DIR" \
    "$IMAGE_NAME" "$@"
elif [ -f "$CONFIG_ABS_PATH" ]; then
  # Montar archivo individual (yaml o py)
  EXT="${CONFIG_ABS_PATH##*.}"
  if [ "$EXT" = "yaml" ] || [ "$EXT" = "yml" ]; then
    DEST="$CONTAINER_CONFIG_DIR/config.yaml"
  elif [ "$EXT" = "py" ]; then
    DEST="$CONTAINER_CONFIG_DIR/config.py"
  else
    echo "ERROR: El archivo debe ser .yaml, .yml o .py"
    exit 2
  fi
  echo "Montando archivo de configuración: $CONFIG_ABS_PATH -> $DEST"
  docker run --rm \
    -v "$CONFIG_ABS_PATH":"$DEST" \
    "$IMAGE_NAME" "$@"
else
  echo "ERROR: $CONFIG_ABS_PATH no existe"
  exit 3
fi
