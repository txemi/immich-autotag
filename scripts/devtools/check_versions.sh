#!/bin/bash
# check_versions.sh
# Muestra la versión en pyproject.toml, el último tag y el estado git

set -e 

echo "Versión en pyproject.toml:"
grep '^version' pyproject.toml || echo "No encontrada"
echo
LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null)
echo "Último tag git: $LATEST_TAG"
echo
GIT_DESCRIBE=$(git describe --tags --always --dirty)
echo "git describe: $GIT_DESCRIBE"
echo
if [[ -n "$LATEST_TAG" ]]; then
    TOML_VERSION=$(grep '^version' pyproject.toml | head -1 | cut -d'=' -f2 | tr -d ' "')
    # Elimina el prefijo 'v' si existe en el tag
    TAG_VERSION=${LATEST_TAG#v}
    if [[ "$TOML_VERSION" != "$TAG_VERSION" ]]; then
        echo -e "\e[31m¡ATENCIÓN! La versión en pyproject.toml ($TOML_VERSION) y el último tag git ($LATEST_TAG) NO coinciden.\e[0m" >&2
        exit 1
    else
        echo -e "\e[32mLa versión en pyproject.toml y el último tag git coinciden.\e[0m"
    fi
else
    echo "No hay tags en el repositorio."
    exit 1
fi
