#!/bin/bash
# Construye y sube la imagen Docker a Docker Hub
# Uso: bash build_and_push.sh

IMAGE_NAME="txemi/immich-autotag:latest"

# Construir la imagen

echo "[INFO] Construyendo la imagen Docker: $IMAGE_NAME"
docker build -t $IMAGE_NAME ../..

# Subir la imagen

echo "[INFO] Subiendo la imagen a Docker Hub: $IMAGE_NAME"
docker push $IMAGE_NAME

echo "[OK] Imagen construida y subida correctamente."
