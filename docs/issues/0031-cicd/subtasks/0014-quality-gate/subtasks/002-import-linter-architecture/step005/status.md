# Import-Linter Architecture Status

## Current Position

- The objectives for STANDARD and TARGET levels are clearly defined (see `objectives.md`).
- The current import-linter configuration enforces some boundaries, but does **not fully achieve** the stated objectives due to tool limitations.

## What Has Been Achieved

- The STANDARD level configuration prevents direct imports of the root `immich_client` package from most modules, but **does not block imports of submodules** (e.g., `immich_client.api.*`).
- The TARGET level configuration attempts to restrict access to `immich_proxy` only to `logging_proxy`, but again, **submodules and indirect imports are not reliably blocked**.
- No true "exception" mechanism exists in import-linter for allowing only one specific module to import a forbidden package; workarounds (like `ignore_imports`) are limited and fragile.

## Limitations

- **Import-linter cannot fully enforce rules involving submodules of external packages** (like `immich_client.*`). It treats external packages as "squashed" modules, so only direct imports are detected.
- **Wildcards and package-level rules** are not always respected for external dependencies.
- **No robust way to allow only one specific module/package as an exception**; the tool is designed for broad boundaries, not fine-grained exceptions.

## Can the Objectives Be Achieved?

- **Not fully with import-linter alone.** The tool's current design does not support the strict, exception-based rules we want for STANDARD and TARGET levels.
- For more precise control, a custom linter, additional static analysis, or a different tool would be needed.

## Summary

- The current setup partially enforces architectural boundaries, but does **not guarantee** the strict objectives defined.
- The limitations are due to how import-linter builds its import graph and handles external packages and exceptions.
- Achieving the exact goals will require either tool improvements or a different approach.
