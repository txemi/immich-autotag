#!/bin/bash
# Ejecuta el script principal con cProfile y guarda el resultado en profile.stats

python -m cProfile -o profile.stats -s cumulative main.py "$@"
echo "Perfil guardado en profile.stats"
echo "Para ver un resumen en texto:"
echo "  python -m pstats profile.stats"
echo "Para visualizarlo gráficamente, instala snakeviz y ejecuta:"
echo "  snakeviz profile.stats"
