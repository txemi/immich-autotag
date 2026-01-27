import tracemalloc
import sys
from pathlib import Path


def print_top(snapshot, key_type='lineno', limit=20):
    print(f"Top {limit} memory allocations:")
    snapshot = snapshot.filter_traces((tracemalloc.Filter(False, "<frozen importlib._bootstrap>"),
                                       tracemalloc.Filter(False, "<unknown>")))
    top_stats = snapshot.statistics(key_type)
    for index, stat in enumerate(top_stats[:limit], 1):
        print(f"#{index}: {stat}")
    other = top_stats[limit:]
    if other:
        size = sum(stat.size for stat in other)
        print(f"{len(other)} other: {size / 1024:.1f} KiB")
    total = sum(stat.size for stat in top_stats)
    print(f"Total allocated size: {total / 1024:.1f} KiB")


def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze_tracemalloc_snapshot.py <snapshot_file>")
        sys.exit(1)
    snapshot_file = Path(sys.argv[1])
    if not snapshot_file.exists():
        print(f"File not found: {snapshot_file}")
        sys.exit(1)
    snapshot = tracemalloc.Snapshot.load(str(snapshot_file))
    print_top(snapshot, key_type='lineno', limit=20)
    print("\nBy file:")
    print_top(snapshot, key_type='filename', limit=10)


if __name__ == "__main__":
    main()
