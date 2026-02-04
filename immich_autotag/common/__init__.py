"""
common/__init__.py

This package contains generic utilities, types, and functions that are independent of the Immich Autotag domain.

Purpose:
- Serves as a "fridge" or repository for reusable, generic, and decoupled code.
- Facilitates reuse and avoids code duplication across different modules of the project.
- MUST NOT contain dependencies on any `immich_autotag` subpackage (such as albums, api, assets, etc.).
- May only depend on the Python standard library and, exceptionally, on very generic external dependencies (e.g., attrs, typing_extensions, etc.).

Usage rules:
- Everything included here should be potentially useful in any other Python project.
- There must be no references to Immich domain logic, types, or specific names.
- If a module in `common` starts depending on business logic, it must be moved out of this package.

Examples of suitable content:
- Type validation utilities, pathlib helpers, generic base classes, generic error wrappers, etc.

Allowed dependencies:
- Python standard library (stdlib)
- Exceptionally: attrs, typing_extensions, enum, etc.

Prohibited dependencies:
- Any `immich_autotag` subpackage
- Business logic, domain models, API, etc.

"""
