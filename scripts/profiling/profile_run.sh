#!/bin/bash
# Run the main script with cProfile and save the result to profile.stats

python -m cProfile -o profile.stats -s cumulative main.py "$@"
echo "Profile saved to profile.stats"
echo "To see a text summary:"
echo "  python -m pstats profile.stats"
echo "To visualize it graphically, install snakeviz and run:"
echo "  snakeviz profile.stats"
