# Subtask: mypy Error Cleanup Plan for Quality Gate

## Context
The Quality Gate in TARGET mode is currently blocked by critical mypy errors (argument types, return types, undefined attributes, etc.). To enable STANDARD mode and ensure code quality, these errors must be reduced to zero.

## Action Plan

### 1. Grouping Critical mypy Errors
- **Argument type mismatches (`arg-type`)**: Methods receiving the wrong client type (`Client` vs `AuthenticatedClient`), or incompatible types (`UUID` vs `str`).
- **Return value type (`return-value`)**: Functions returning `None` when a concrete type is required, or returning the wrong type.
- **Undefined/missing attributes**: Methods or attributes that do not exist or are misnamed.
- **Too many arguments (`call-arg`)**: Calls with too many or too few arguments.
- **Unsupported class scoped import**: Imports inside classes or functions not supported by mypy.

### 2. Optimal Strategy
- **Unify client type** in proxy functions and their calls.
- **Adjust return types** so functions never return `None` if the type does not allow it.
- **Move imports** out of classes/functions to the top of the file.
- **Fix misnamed attributes** (`get_client` → `_client`, etc.).

### 3. Goal
Reduce the number of critical mypy errors to zero to unblock the Quality Gate in TARGET mode and enable STANDARD mode.

### 4. Priority
1. **Client/AuthenticatedClient block** and return types: most numerous and easiest to clean up in bulk.
2. **Imports and attributes**: fix import and attribute naming errors.
3. **Other errors**: address remaining errors one by one.

---

**This document should be updated with progress and decisions made during the cleanup.**
