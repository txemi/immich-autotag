#!/bin/bash
# Script to show the current status of the Quality Gate in CHECK mode (no changes applied)

bash "$(dirname "$0")/quality_gate.sh" --level=STANDARD --mode=CHECK
