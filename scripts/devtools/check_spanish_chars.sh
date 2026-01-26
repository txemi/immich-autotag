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
EXCLUDES=".git,.venv,.mypy_cache,node_modules,dist,build,jenkins_logs,__pycache__,scripts/devtools/check_spanish_chars.sh,logs_local"

# Find Spanish/accented characters and common Spanish words in comments

EXCLUDE_ARGS=$(printf -- '--exclude-dir=%s ' $(echo $EXCLUDES | tr ',' ' '))
SCRIPT_PATH="$SCRIPT_DIR/check_spanish_chars.sh"


# List of common Spanish words, one per line for readability
SPANISH_WORDS='si
solo
mantenemos
compatibilidad
devolviendo
lista
soporta
estructura
necesitaría
cambiado
tenemos
usamos
comentario
ejemplo
devuelve
más
menos
muy
también
aquí
allí
aquellos
aquellas
todavía
aún
quizá
quizás
siempre
nunca
jamás
antes
después
hoy
mañana
ayer
entonces
luego
mientras
durante
nuevo
nueva
nuevos
nuevas
viejo
vieja
viejos
viejas
primero
primera
primeros
primeras
último
última
últimos
últimas
mejor
peor
mayor
menor
grande
pequeño
pequeña
pequeños
pequeñas
importante
interesante
difícil
fácil
rápido
lento
posible
imposible
correcto
incorrecto
verdadero
falso
cierto
seguro
probable
improbable
claro
oscuro
complicado
complejo
sencillo'

# Build the Spanish word pattern for grep
SPANISH_WORD_PATTERN=$(echo "$SPANISH_WORDS" | paste -sd '|' -)
SPANISH_PATTERN="[áéíóúÁÉÍÓÚñÑüÜ¿¡]|\\b(${SPANISH_WORD_PATTERN})\\b"
files_to_check=$(git ls-files)


# Search for Spanish characters/words in the git-tracked files
spanish_matches=$(echo "$files_to_check" | xargs grep -n -I -E "$SPANISH_PATTERN" || true)

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
