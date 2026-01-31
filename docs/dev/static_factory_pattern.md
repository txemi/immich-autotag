# 1. Static Factory Pattern for attrs Classes with Private Attributes

- [1. Static Factory Pattern for attrs Classes with Private Attributes](#1-static-factory-pattern-for-attrs-classes-with-private-attributes)
  - [1.1. Context](#11-context)
  - [1.2. Example](#12-example)
  - [1.3. Rationale](#13-rationale)
  - [1.4. See also](#14-see-also)

## 1.1. Context

In this project, we use `attrs` for robust, type-safe data classes. For classes with private attributes (e.g., `_state`, `_max_age_seconds`), we enforce the following pattern:

- All private attributes are declared with `init=False` and strict type validators.
- The class is instantiated with a no-argument constructor (`cls()`), and attributes are set manually in static factory methods.
- All construction must go through static factory methods (e.g., `from_dto`, `from_cache_dict`, `_from_state`).
- This pattern is necessary to:
  - Avoid exposing private fields in the public constructor.
  - Allow robust type validation and encapsulation.
  - Satisfy linters, mypy, and defensive programming requirements.

## 1.2. Example

```python
@attrs.define(auto_attribs=True, slots=True)
class AssetCacheEntry:
    _state: AssetDtoState = attrs.field(init=False, validator=attrs.validators.instance_of(AssetDtoState))
    _max_age_seconds: int = attrs.field(init=False, validator=attrs.validators.instance_of(int))

    @classmethod
    def _from_state(cls, *, state: AssetDtoState, max_age_seconds: int) -> "AssetCacheEntry":
        self = cls()
        self._state = state
        self._max_age_seconds = max_age_seconds
        return self
```

## 1.3. Rationale

- This approach is robust against accidental misuse and future refactors.
- It is compatible with type checkers and linters.
- It is the recommended way to combine private attributes, type safety, and static factory construction in Python with `attrs`.

## 1.4. See also
- `immich_autotag/assets/asset_cache_entry.py`
- `immich_autotag/assets/asset_dto_state.py`

---

*Decision date: 2026-01-31*
*Pattern enforced by automation and code review.*
