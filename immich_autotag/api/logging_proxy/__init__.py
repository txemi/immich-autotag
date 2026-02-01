"""
Logging Proxy Layer

This layer wraps the immich_proxy functions to add automatic event logging,
statistics tracking, and modification reporting. It's the bridge between
business logic and technical API calls.

Pattern:
  - immich_proxy/*: Pure API calls (no side effects)
  - logging_proxy/*: API calls + event logging + statistics
"""
