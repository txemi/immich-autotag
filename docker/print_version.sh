#!/bin/bash
# print_version.sh
# Muestra la versión instalada de immich-autotag en el contenedor
set -e
python3 -c "import immich_autotag.version as v; print(f'Immich AutoTag versión: {v.__version__}  commit: {getattr(v, '__git_commit__', 'N/A')}')"
