#!/bin/bash
# Script para formatear y organizar imports en todo el proyecto

# Activa el entorno virtual si es necesario
# source /ruta/a/tu/entorno/.venv/bin/activate

# Formatea el código con Black
black .

# Organiza los imports con isort
isort .
