#!/usr/bin/env python3
"""Check that repo_policy.yaml exists at the repo root, parses, and has the four required sections."""
import sys

REQUIRED = ["fuente_de_verdad", "espejo", "respaldo_offsite", "ci"]

try:
    import yaml
except ImportError:
    print("repo_policy_check: PyYAML is missing on this agent, so the file cannot be parsed. "
          "This is NOT a pass.", file=sys.stderr)
    sys.exit(1)

try:
    data = yaml.safe_load(open("repo_policy.yaml", encoding="utf-8")) or {}
except FileNotFoundError:
    print("repo_policy_check: repo_policy.yaml is missing at the repo root", file=sys.stderr)
    sys.exit(1)
missing = [k for k in REQUIRED if k not in data]
if missing:
    print(f"repo_policy_check: required sections missing: {missing}", file=sys.stderr)
    sys.exit(1)
print("repo_policy_check: repo_policy.yaml parses and has " + ", ".join(REQUIRED) + ".")
