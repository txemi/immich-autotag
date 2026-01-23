# Coding Style Guide

## Explicit Attribute Access and Type Safety

In this project, **dynamic attribute access functions** such as `getattr`, `setattr`, and `hasattr` are strictly **forbidden** for accessing known attributes in models, DTOs, or domain classes. Always use **explicit attribute access** and static type checking wherever possible.

### Forbidden Example
```python
# DO NOT USE
value = getattr(obj, 'field')
if hasattr(obj, 'field'):
    ...
```

### Preferred Example
```python
# USE THIS
value = obj.field  # Direct access
if isinstance(obj.field, ExpectedType):
    ...
```

## Rationale
- **Readability:** Explicit access makes it clear which attributes are used and simplifies code review.
- **Maintainability:** Prevents subtle bugs from refactoring or attribute renaming.
- **Type Safety:** Enables static analysis tools (mypy, flake8, etc.) to catch errors early.
- **Debugging:** Access errors are detected during development, not in production.

## Style Rules
1. **Never use dynamic attribute access for known fields.**
2. **Always document expected attributes in classes and DTOs.**
3. **Use type hints in all methods and properties.**
4. **If an attribute may be missing, document the behavior and use explicit checks.**
5. **If you need to access multiple attributes, use a list of names and access each one directly, never with getattr.**

## Robust Function Example
```python
def get_dates(asset: AssetResponseDto) -> list[datetime]:
    dates = []
    for attr in ["created_at", "file_created_at", "file_modified_at", "local_date_time"]:
        value = getattr(asset, attr, None)
        if value is not None and isinstance(value, datetime):
            dates.append(value)
    return dates
```

> **Note:** While `getattr` is used here to avoid code duplication, in main project logic always prefer direct access (`asset.created_at`, etc.) and only allow it in tightly controlled utility functions.

## Why We Insist On This
All contributors must follow this style to avoid hard-to-detect bugs and facilitate collaboration. If in doubt, ask before using any dynamic attribute function.

---

## Models and Class Types
- **Do NOT use Python `@dataclass` for new models or DTOs.**
- **Use `pydantic` models** (e.g. `pydantic.BaseModel`) for classes that are serialized, used as DTOs, or exchanged with external services (HTTP APIs, clients). Pydantic provides explicit validation, parsing, and consistent serialization.
- **Use `attrs`** (`attrs.define` / `attrs.dataclass` style) for internal/domain classes that contain logic, mutability rules, or non-trivial behaviour and are not intended primarily for direct serialization. `attrs` provides concise declarations and good runtime performance.

### Examples
**Serializable DTO:**
```python
from pydantic import BaseModel

class AssetDto(BaseModel):
    id: str
    filename: str
```

**Internal/domain class:**
```python
import attrs

@attrs.define(auto_attribs=True, on_setattr=attrs.setters.validate)
class Album:
    id: str = attrs.field(validator=attrs.validators.instance_of(str))
    name: str = attrs.field(validator=attrs.validators.instance_of(str))

    def rename(self, new_name: str) -> None:
        self.name = new_name
```

**Incorrect:**
```python
from dataclasses import dataclass

@dataclass
class Model:
    id: str
    name: str
```

---

**Last review:** 2026-01-23
**Maintainer:** txemi
