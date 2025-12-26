# Duplicate Asset Management in Immich: Problem Statement and Solution Plan

## Context

After investigating the Immich API and its capabilities, we discovered that Immich already maintains a comprehensive database of duplicate assets. This greatly simplifies our approach to duplicate detection and management.

## Key Findings

- Immich exposes a dedicated endpoint for retrieving all duplicate assets:
  - Official documentation: https://api.immich.app/endpoints/duplicates/getAssetDuplicates
- The response from this endpoint is a large structure containing all known duplicates, and retrieving it may take some time.
- Each asset's metadata also includes a field listing its duplicates, allowing direct access to related assets.

## Design Decisions

- **No direct use of requests or manual HTTP calls:**
  We will use the high-level Immich client library already integrated in the project for all API interactions, ensuring consistency and maintainability.
- **Wrapper class for duplicates:**
  We will create a dedicated wrapper class for the duplicates database, similar to the wrappers already used for albums and tags. This class will encapsulate the duplicate data and provide convenient access methods.
- **Context integration:**
  The main context object (which already holds the album and tag wrappers) will be extended to include the duplicates wrapper. This ensures that duplicate information is readily available throughout the main processing flow.
- **Early loading:**
  The duplicates database will be loaded at the start of the main execution flow, right after albums and tags. This allows all subsequent logic to leverage duplicate information efficiently.
- **Asset-level duplicate access:**
  When loading asset metadata, we will utilize the `duplicates` field to quickly access all related duplicate assets. This enables logic such as propagating good metadata (e.g., album assignment) from one duplicate to all others.

## Next Steps

1. Implement a wrapper class for the duplicates database using the project's standard class construction approach (attrs, typeguard, etc.).
2. Update the main context class to include the duplicates wrapper.
3. Ensure the main execution flow loads the duplicates database at startup, after albums and tags.
4. Refactor asset logic to leverage the duplicates information for tasks such as album assignment, tag propagation, and more.

## Motivation

By leveraging Immich's built-in duplicate management, we can:
- Avoid reinventing duplicate detection logic.
- Ensure consistency with Immich's internal view of duplicates.
- Simplify and accelerate downstream logic that depends on asset relationships.

---

This document serves as the requirements and design foundation for all future work related to duplicate asset management in this project.
