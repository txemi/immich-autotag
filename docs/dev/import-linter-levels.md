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
- ⚠️ Asset cache entry isolation (currently broken)
- ⚠️ Asset response wrapper isolation (currently broken)

**Status:** ⚠️ Some contracts broken (3 kept, 2 broken)

**Purpose:** Ensure better architecture before releases. The broken contracts are known technical debt.

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

# TARGET level (uses importlinter-target.ini - 5 contracts, 2 broken)
bash scripts/devtools/quality_gate.sh --level=TARGET --mode=CHECK

# STRICT level (uses importlinter-strict.ini - 5 contracts, 2 broken)
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

## Current Status

- **STANDARD:** ✅ All contracts pass (2 kept, 0 broken)
- **TARGET:** ⚠️ Some contracts broken (3 kept, 2 broken)
- **STRICT:** ⚠️ Same as TARGET (3 kept, 2 broken)

The broken contracts in TARGET/STRICT are known technical debt related to circular dependencies through `ImmichContext` and can be addressed in future refactoring efforts.
