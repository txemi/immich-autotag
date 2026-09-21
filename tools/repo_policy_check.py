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
if not isinstance(data, dict):
    print("repo_policy_check: repo_policy.yaml must be a mapping of sections, not a list or a scalar",
          file=sys.stderr)
    sys.exit(1)
# A key with no value (`ci:`) parses to None: present, but it declares nothing.
missing = [k for k in REQUIRED if not isinstance(data.get(k), dict) or not data[k]]
if missing:
    print(f"repo_policy_check: required sections missing or empty: {missing}", file=sys.stderr)
    sys.exit(1)
print("repo_policy_check: repo_policy.yaml parses and has " + ", ".join(REQUIRED) + ".")
