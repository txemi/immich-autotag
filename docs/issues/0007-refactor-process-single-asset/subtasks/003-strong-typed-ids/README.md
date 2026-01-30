# Subtask 003: Strongly Typed IDs for Asset, Tag, and Album

## Context and Motivation

Currently, the project uses UUIDs (universally unique identifiers) as the natural identifiers for assets, albums, and tags, as per the Immich API. However, all these IDs are represented as plain UUIDs or strings, which can lead to logical errors: mixing up asset, tag, and album IDs in code, passing the wrong type, or comparing unrelated entities.

To enforce type safety and prevent these classes of bugs, we want to introduce **strongly typed wrappers** for each kind of identifier:
- `AssetUUID`
- `TagUUID`
- `AlbumUUID`

This will allow the type checker (mypy, Pyright, etc.) and runtime checks to catch accidental mixing of IDs, and make the code more self-documenting and robust.

## Goals
- Prevent accidental comparison or mixing of asset, tag, and album IDs.
- Enforce type safety at both static (type checker) and runtime levels.
- Provide a reusable, clear pattern for all entity IDs.
- Begin migration of codebase to use these wrappers.

## Plan
1. **Review and reinforce the current `AssetUUID` class** to ensure it does not allow comparison or operations with other types (including other UUID wrappers).
2. **Design a reusable pattern** (base class, mixin, or similar) for UUID wrappers that enforces type safety but does not allow cross-type operations, even with inheritance.
3. **Implement `TagUUID` and `AlbumUUID`** following this pattern.
4. **Document the pattern and rationale** in this subtask.
5. **Search and list code locations** where tag and album IDs are used, and plan the migration.
6. **(Optional) Start replacing usages** in the codebase, prioritizing critical logic.

## Design Considerations
- Each wrapper must only allow comparison and operations with its own type.
- Attempting to compare or operate with a different type (even another UUID wrapper) should raise an exception or fail type checking.
- The pattern should be clear and maintainable for future entity types.

---

## Implementation Steps
- [ ] Review and refactor `AssetUUID` for strict type safety.
- [ ] Propose and document the reusable pattern.
- [ ] Implement `TagUUID` and `AlbumUUID`.
- [ ] Document the pattern and migration plan here.
- [ ] List code locations for migration.
- [ ] (Optional) Start migration.

---

*Created automatically by GitHub Copilot on 2026-01-30.*
