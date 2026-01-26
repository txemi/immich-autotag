#!/bin/bash
# Spanish language character check (robust project root detection)
# Usage: ./check_spanish_chars.sh [target_dir]

# Detect project root (directory containing this script, then up one level)
set -e
set -x
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR" | xargs dirname)"

# Set the target directory to project root unless overridden by argument
TARGET_DIR="${1:-$PROJECT_ROOT}"

# Exclude common build and dependency folders
EXCLUDES=".git,.venv,.mypy_cache,node_modules,dist,build,logs_local,jenkins_logs,__pycache__,scripts/devtools/check_spanish_chars.sh"

# Find Spanish/accented characters and common Spanish words in comments
EXCLUDE_ARGS=$(printf -- '--exclude-dir=%s ' $(echo $EXCLUDES | tr ',' ' '))
SPANISH_PATTERN='[áéíóúÁÉÍÓÚñÑüÜ¿¡]|\b(si|solo|mantenemos|compatibilidad|devolviendo|lista|uno|cero|mapa|soporta|estructura|necesitaría|cambiado|no|tenemos|usamos|comentario|ejemplo|devuelve|el|la|los|las|un|una|unos|unas|por|para|con|sin|sobre|entre|pero|porque|cuando|donde|como|más|menos|muy|también|aquí|allí|este|ese|esa|estos|esas|aquellos|aquellas|ya|todavía|aún|quizá|quizás|siempre|nunca|jamás|antes|después|hoy|mañana|ayer|ahora|entonces|luego|mientras|durante|despues|antes|nuevo|nueva|nuevos|nuevas|viejo|vieja|viejos|viejas|primero|primera|primeros|primeras|último|última|últimos|últimas|mejor|peor|mayor|menor|grande|pequeño|pequeña|pequeños|pequeñas|importante|interesante|difícil|fácil|rápido|lento|posible|imposible|correcto|incorrecto|verdadero|falso|cierto|seguro|probable|improbable|claro|oscuro|simple|complicado|complejo|sencillo|difícil|fácil|rápido|lento|posible|imposible|correcto|incorrecto|verdadero|falso|cierto|seguro|probable|improbable|claro|oscuro|simple|complicado|complejo|sencillo)\b'
spanish_matches=$(grep -r -n -I -E "$SPANISH_PATTERN" "$TARGET_DIR" $EXCLUDE_ARGS --exclude=*.json --exclude=*.data.json --exclude=*.pyc --exclude=*.pyo || true)

if [ -n "$spanish_matches" ]; then
	echo '❌ Spanish language characters detected in the following files/lines:'
	echo "$spanish_matches"
	# Count unique files with matches
	file_count=$(echo "$spanish_matches" | cut -d: -f1 | sort | uniq | wc -l)
	echo "Files remaining to translate: $file_count"
	exit 1
else
	echo "✅ No Spanish language characters detected."
	echo "Files remaining to translate: 0"
	exit 0
fi
