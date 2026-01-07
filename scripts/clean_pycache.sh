#!/bin/bash
# Cleans all .pyc files and __pycache__ folders in the project

find . -name "__pycache__" -type d -exec rm -rf {} +
find . -name "*.pyc" -type f -delete

echo "Cleanup of .pyc files and __pycache__ folders completed."
