# Feature: Filter assets by links in configuration

## Context
Sometimes, when analyzing assets (photos, videos) with many duplicates or conflicts, it is difficult to identify the root cause just by looking at the log, especially when there are many duplicates. To facilitate analysis, this feature allows the user to filter processing to focus only on specific assets.

## Feature Description
- The user can specify in the configuration file a list of links (URLs or IDs) of assets to analyze.
- If the list is empty or does not exist, the current behavior remains: all assets are processed.
- If the list contains elements, **only** those assets will be processed.
- When the filter is active, verbose mode (detailed logging) will be automatically enabled to aid diagnosis.
- The goal is to let the user focus on problematic cases and get all relevant information for those assets without noise from other processes.

## Example configuration
```yaml
# user_config.yaml
filter_asset_links:
  - https://my.immich/asset/123456
  - https://my.immich/asset/abcdef
  # Or direct IDs:
  - 123456
  - abcdef
```

## Technical details
- The configuration field could be called `filter_asset_links` or similar.
- The system should accept both full URLs and direct asset IDs.
- If the filter is active, the system must force verbose mode.
- Filtering should be applied during the asset loading phase, before any processing.

## Motivation
This feature will allow much more efficient debugging and analysis of problematic cases, especially in situations with many duplicates or conflicts that are hard to track with only the global log.

---

*This document was automatically generated to specify the new feature before implementation.*
