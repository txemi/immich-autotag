# Issue 0015: GitHub Actions PyPI Publishing

**Status**: Resolved  
**Created**: 2026-01-14  
**Resolved**: 2026-01-14  
**Version**: v0.70  
**Related GitHub Issue**: [#32](https://github.com/txemi/immich-autotag/issues/32)

## Problem Statement

GitHub Actions workflow for automated PyPI publishing was disabled (`release.yml.disabled`) because the immich-client library setup required access to a real Immich server to detect the API version. This worked in local environments and Jenkins (where config files with server credentials exist), but failed in GitHub Actions CI/CD environment.

### Root Cause

The `setup_venv.sh` script attempts to:
1. Read Immich server configuration from `~/.config/immich_autotag/config.py`
2. Connect to the Immich server API to detect version (e.g., v2.4.1)
3. Download the matching OpenAPI spec from GitHub
4. Generate the immich-client library using openapi-python-client

In GitHub Actions, there is no:
- Configuration file with server credentials
- Access to a private Immich server
- API key for authentication

This caused the script to fail or use the 'main' branch spec (unreliable).

## Solution Implemented

### 1. Hardcoded Version Fallback in `setup_venv.sh`

Added a default fallback version that matches the common deployment version:

```bash
# Default fallback version (matches common deployment v2.4.1)
DEFAULT_IMMICH_VERSION="v2.4.1"

# Get server version and construct OpenAPI spec URL
if [ -n "$IMMICH_HOST" ] && [ -n "$IMMICH_PORT" ] && [ -n "$IMMICH_API_KEY" ]; then
    echo "Connecting to Immich at http://$IMMICH_HOST:$IMMICH_PORT to detect version..."
    IMMICH_VERSION=$(get_immich_version "$IMMICH_HOST" "$IMMICH_PORT" "$IMMICH_API_KEY")
    echo "Detected Immich version: $IMMICH_VERSION"
else
    echo "WARNING: Could not read Immich config. Config values: host='$IMMICH_HOST' port='$IMMICH_PORT' api_key_length=${#IMMICH_API_KEY}"
    echo "WARNING: Using default OpenAPI spec version: $DEFAULT_IMMICH_VERSION"
    IMMICH_VERSION="$DEFAULT_IMMICH_VERSION"
fi
```

**Behavior:**
- **With configuration** (Jenkins, local development): Auto-detects version from server
- **Without configuration** (GitHub Actions): Uses hardcoded v2.4.1

### 2. Enabled GitHub Actions Workflow

- Renamed `.github/workflows/release.yml.disabled` → `.github/workflows/release.yml`
- Added system dependencies installation (curl)
- Added documentation comments explaining the fallback mechanism

### 3. Updated Workflow Configuration

Added curl installation step:
```yaml
- name: Install system dependencies
  run: |
    sudo apt-get update
    sudo apt-get install -y curl
```

## Benefits

1. ✅ **Doesn't break Jenkins**: Auto-detection still works when config is available
2. ✅ **Unblocks GitHub Actions**: Uses stable known version (v2.4.1)
3. ✅ **Maintainable**: Easy to update `DEFAULT_IMMICH_VERSION` constant
4. ✅ **Secure for CI/CD**: No credentials or private server access required
5. ✅ **Reliable**: Uses specific version tag instead of unstable 'main' branch

## Testing

Verified the script works without configuration:

```bash
$ bash -c 'source setup_venv.sh 2>&1' | grep -E "WARNING|version:|Using OpenAPI"
WARNING: Could not read Immich config. Config values: host='' port='' api_key_length=0
WARNING: Using default OpenAPI spec version: v2.4.1
Using OpenAPI spec from: https://raw.githubusercontent.com/immich-app/immich/v2.4.1/open-api/immich-openapi-specs.json
```

## Version Update Strategy

When Immich server is upgraded to a new version:

1. Update `DEFAULT_IMMICH_VERSION` in `setup_venv.sh`
2. Test locally with the new version
3. Commit and push changes
4. GitHub Actions will use the new version on next release

## Implementation Details

**Branch**: `fix/github-actions-immich-client-setup`  
**Commit**: `2652c5c`  
**Modified Files**:
- `setup_venv.sh` - Added fallback version logic
- `.github/workflows/release.yml` - Enabled and updated workflow

## Related Documentation

- GitHub Issue: [#32 Enable automated PyPI publishing via GitHub Actions](https://github.com/txemi/immich-autotag/issues/32)
- Script: [`setup_venv.sh`](../../../setup_venv.sh)
- Workflow: [`.github/workflows/release.yml`](../../../.github/workflows/release.yml)

## Next Steps

1. ✅ Create feature branch
2. ✅ Implement solution
3. ✅ Test without configuration
4. ✅ Document in issue system
5. ⏳ Push branch to remote
6. ⏳ Create Pull Request to develop
7. ⏳ Test GitHub Actions workflow
8. ⏳ Merge to main when stable
