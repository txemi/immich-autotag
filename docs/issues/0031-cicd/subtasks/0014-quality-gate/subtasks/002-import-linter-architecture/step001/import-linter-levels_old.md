# Import-Linter Configuration - Quality Levels

This project uses **import-linter** to enforce architectural boundaries through import contracts. Different quality levels have different levels of enforcement.

## Configuration Files

- **`importlinter.ini`** (STANDARD level)
  - Used in CI/CD pipelines
  - Only critical architectural boundaries
  - Must always pass

- **`importlinter-target.ini`** (TARGET level)
  - Used for release validation
  - Includes STANDARD contracts + additional module isolation rules
  - Stricter than STANDARD

- **`importlinter-strict.ini`** (STRICT level)
  - Maximum enforcement for future improvements
  - Includes all TARGET contracts + potential future rules
  - Currently equivalent to TARGET

## Quality Levels

### STANDARD (CI/CD)
**Contracts enforced:**
- ✅ Only logging_proxy can access immich_proxy
- ✅ Only immich_proxy can access immich_client

**Status:** ✅ All contracts pass (2 kept, 0 broken)

**Purpose:** Fast feedback loop for developers, enforcing only critical architectural boundaries that must never be violated.

### TARGET (Release)
**Contracts enforced:**
- All STANDARD contracts (2)
- ✅ Asset manager isolation from albums
- ✅ Only logging_proxy should import immich_proxy modules
- ⚠️ Asset cache entry isolation (currently broken)
- ⚠️ Asset response wrapper isolation (currently broken)

**Status:** ⚠️ Some contracts broken (4 kept, 2 broken)

**Purpose:** Ensure better architecture before releases. The broken contracts are known technical debt related to circular dependencies through ImmichContext.

### STRICT (Future)
**Contracts enforced:**
- All TARGET contracts
- (Space for additional future contracts)

**Purpose:** Reserved for even stricter rules as the architecture evolves.

## Usage

The quality gate script automatically selects the appropriate configuration file based on the `--level` parameter:

```bash
# STANDARD level (uses importlinter.ini - 2 contracts, all pass)
bash scripts/devtools/quality_gate.sh --level=STANDARD --mode=CHECK

# TARGET level (uses importlinter-target.ini - 6 contracts, 2 broken)
bash scripts/devtools/quality_gate.sh --level=TARGET --mode=CHECK

# STRICT level (uses importlinter-strict.ini - 6 contracts, 2 broken)
bash scripts/devtools/quality_gate.sh --level=STRICT --mode=CHECK
```

All levels execute import-linter, but with different configuration files that enforce different sets of contracts.

## Manual Verification

You can manually check contracts using:

```bash
# Remove cache for clean run
rm -rf .import_linter_cache

# Check STANDARD contracts
.venv/bin/lint-imports --config importlinter.ini

# Check TARGET contracts
.venv/bin/lint-imports --config importlinter-target.ini

# Check STRICT contracts
.venv/bin/lint-imports --config importlinter-strict.ini
```

## Adding New Contracts

1. **For CI/CD enforcement:** Add to `importlinter.ini` (use sparingly!)
2. **For release enforcement:** Add to `importlinter-target.ini` and `importlinter-strict.ini`
3. **For future strictness:** Add only to `importlinter-strict.ini`

## Contract Reference

### STANDARD Contracts

#### 1. Only logging_proxy can access immich_proxy
- **Source:** All of immich_autotag
- **Forbidden:** immich_autotag.api.immich_proxy (package level)
- **Purpose:** Prevent direct access to proxy internals
- **Status:** ✅ KEPT

#### 2. Only immich_proxy can access immich_client
- **Source:** All of immich_autotag
- **Forbidden:** immich_client (external package)
- **Purpose:** Ensure all external API calls go through proxy layer
- **Status:** ✅ KEPT

### TARGET Additional Contracts

#### 3. Only logging_proxy should import immich_proxy modules
- **Source:** All of immich_autotag
- **Forbidden:** 
  - immich_autotag.api.immich_proxy.users
  - immich_autotag.api.immich_proxy.assets
  - immich_autotag.api.immich_proxy.search
  - immich_autotag.api.immich_proxy.tags
  - immich_autotag.api.immich_proxy.albums
- **Purpose:** Direct proxy functions should only be called by logging_proxy layer
- **Status:** ✅ KEPT

#### 4. Asset manager isolation from albums
- **Source:** immich_autotag.assets.asset_manager
- **Forbidden:** immich_autotag.albums.album_collection_wrapper
- **Purpose:** Prevent circular dependencies
- **Status:** ✅ KEPT

#### 5. Asset cache entry isolation (BROKEN)
- **Source:** immich_autotag.assets.asset_cache_entry
- **Forbidden:** asset_manager, asset_response_wrapper, album_collection_wrapper
- **Issue:** Circular dependency through ImmichContext
- **Status:** ⚠️ BROKEN

#### 6. Asset response wrapper isolation (BROKEN)
- **Source:** immich_autotag.assets.asset_response_wrapper
- **Forbidden:** asset_manager, album_collection_wrapper
- **Issue:** Circular dependency through ImmichContext
- **Status:** ⚠️ BROKEN

## Current Status Summary

| Level | Config File | Contracts | Kept | Broken | Status |
|-------|-------------|-----------|------|--------|--------|
| STANDARD | importlinter.ini | 2 | 2 | 0 | ✅ PASS |
| TARGET | importlinter-target.ini | 6 | 4 | 2 | ⚠️ PARTIAL |
| STRICT | importlinter-strict.ini | 6 | 4 | 2 | ⚠️ PARTIAL |

The broken contracts in TARGET/STRICT are known technical debt that can be addressed in future refactoring efforts to untangle the ImmichContext dependencies.
