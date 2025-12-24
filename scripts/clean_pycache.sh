#!/bin/bash
# Limpia todos los archivos .pyc y carpetas __pycache__ en el proyecto

find . -name "__pycache__" -type d -exec rm -rf {} +
find . -name "*.pyc" -type f -delete

echo "Limpieza de .pyc y __pycache__ completada."
