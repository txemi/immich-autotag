
#!/bin/bash
# Script portable para arrancar el contenedor Docker de immich-autotag montando config
# Uso: bash scripts/run_docker_with_config.sh <ruta_local_config> [opciones_docker]




IMAGE_NAME="immich-autotag:latest"
# El usuario del contenedor es autotaguser, su home es /home/autotaguser
CONTAINER_CONFIG_DIR="/home/autotaguser/.config/immich_autotag"
# Directorio de salida fijo para Docker en el host y en el contenedor
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOST_OUTPUT_DIR="$SCRIPT_DIR/../docker_output"
CONTAINER_OUTPUT_DIR="/home/autotaguser/immich_autotag_output"

# Crear el directorio de salida si no existe
mkdir -p "$HOST_OUTPUT_DIR"

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



# Convertir ruta de config a absoluta
CONFIG_ABS_PATH="$(realpath "$CONFIG_LOCAL_PATH")"


# Construir opciones de volumen (config y salida fija)
VOLUMES=""
if [ -d "$CONFIG_ABS_PATH" ]; then
  echo "Montando directorio de configuración: $CONFIG_ABS_PATH -> $CONTAINER_CONFIG_DIR"
  VOLUMES+="-v $CONFIG_ABS_PATH:$CONTAINER_CONFIG_DIR "
elif [ -f "$CONFIG_ABS_PATH" ]; then
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
  VOLUMES+="-v $CONFIG_ABS_PATH:$DEST "
else
  echo "ERROR: $CONFIG_ABS_PATH no existe"
  exit 3
fi

# Montar siempre el directorio de salida fijo
echo "Montando directorio de salida: $HOST_OUTPUT_DIR -> $CONTAINER_OUTPUT_DIR"
VOLUMES+="-v $HOST_OUTPUT_DIR:$CONTAINER_OUTPUT_DIR "

docker run --rm $VOLUMES "$IMAGE_NAME" "$@"
