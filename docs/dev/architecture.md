# Project Architecture

## Package Structure and Responsibilities

### `immich_autotag/albums/`
- **Purpose:** Core logic and abstractions for albums (wrappers, collection, CRUD, policies).
- **Responsibilities:**
  - Manipulation and representation of albums.
  - No asset-specific business logic or assignment logic.
- **Dependencies:**
  - MUST NOT depend on `assets` or any asset business logic.
  - Can be used by other modules for generic album manipulation.

### `immich_autotag/assets/albums/`
- **Purpose:** Business logic relating assets and albums.
- **Responsibilities:**
  - Detection, assignment, conditional creation, temporary album logic, etc.
  - Handles the relationship between assets and albums.
- **Dependencies:**
  - May import/use `albums` for wrappers and general utilities.
  - MUST NOT be imported from `albums` (do not invert the dependency).

### `immich_autotag/assets/albums/temporary_manager/`
- **Purpose:** Encapsulates all logic related to temporary albums.
- **Responsibilities:**
  - Creation, health check, cleanup, and recreation of temporary albums.
  - Provides a clear API for managing temporary albums in the context of asset processing.
- **Dependencies:**
  - May use `albums` and `assets` as needed, but should not be imported by core album logic.

## Dependency Rules
- `albums/` is the core and must remain independent of asset-specific logic.
- `assets/albums/` can use `albums/` but not the other way around.
- Temporary album logic is isolated in its own subpackage for clarity and maintainability.

## Visual Overview
```
immich_autotag/
  albums/
    ... (core album logic)
  assets/
    albums/
      ... (asset-album business logic)
      temporary_manager/
        ... (temporary album logic)
```

## Notes
- This structure ensures clear separation of concerns, maintainability, and ease of onboarding for new contributors.
- For any logic that relates to the relationship between assets and albums, always use the `assets/albums/` package.
- For core album manipulation, use the `albums/` package.
