#!/bin/bash
# Script para mostrar el estado actual del Quality Gate en modo CHECK (sin aplicar cambios)

bash "$(dirname "$0")/quality_gate.sh" --level=STANDARD --mode=CHECK
