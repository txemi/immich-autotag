# common/README.md

# `common` package

This package acts as a "fridge" or repository for generic and reusable code for the `immich_autotag` project.

## Purpose
- Centralize utilities, types, and functions that do NOT depend on the Immich domain or business logic.
- Facilitate reuse and avoid code duplication across different modules.
- Serve as a base for code that could be extracted to an independent library in the future.

## Usage rules
- **Must not** import or depend on any `immich_autotag` subpackage (such as `albums`, `api`, `assets`, etc.).
- May only depend on the Python standard library and, exceptionally, on very generic external dependencies (e.g., `attrs`, `typing_extensions`, `enum`, etc.).
- Everything included here should be potentially useful in any other Python project.
- If a module in `common` starts depending on business logic, it must be moved out of this package.

## Examples of suitable content
- Type validation utilities
- `pathlib` helpers
- Generic base classes
- Generic error wrappers
- Generic serialization/deserialization functions

## Allowed dependencies
- Python standard library (stdlib)
- Exceptionally: `attrs`, `typing_extensions`, `enum`, etc.

## Prohibited dependencies
- Any `immich_autotag` subpackage
- Business logic, domain models, API, etc.

---

> **IMPORTANT:**
> The goal of this package is to keep the code generic, clean, and decoupled. If you are unsure whether something belongs here, it probably does not.
