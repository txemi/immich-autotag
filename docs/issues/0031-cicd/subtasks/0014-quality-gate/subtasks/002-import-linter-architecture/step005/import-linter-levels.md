# Import-Linter Configuration - Quality Levels

This document describes the quality levels and architecture rules applied with import-linter in this project. Each level defines which contracts apply and how boundaries between modules are enforced.

## Quality levels

### STANDARD (CI/CD)
- Only logging_proxy can access immich_proxy
- Only immich_proxy can access immich_client

### TARGET (Release)
- Includes STANDARD rules
- Adds isolation rules between modules (stricter)

### STRICT (Future)
- Maximum restriction, includes all previous and possible future rules

## Purpose
- STANDARD: fast feedback and avoid major violations
- TARGET: architecture validation for releases
- STRICT: experimentation and continuous improvement

## Current status
- All STANDARD contracts pass
- TARGET and STRICT may have broken rules in development

---

(Contenido movido desde docs/dev/import-linter-levels.md)
