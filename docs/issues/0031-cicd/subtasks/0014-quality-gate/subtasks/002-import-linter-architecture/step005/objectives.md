# Import-Linter Architecture Objectives

## STANDARD Level Objective

Only the package `immich_autotag.api.immich_proxy*` (including all its submodules) is allowed to import from the external library `immich_client*` (including all its submodules). No other package or module in `immich_autotag*` may import anything from `immich_client*`.

## TARGET Level Objective

Only the package `immich_autotag.api.logging_proxy*` (including all its submodules) is allowed to import from `immich_autotag.api.immich_proxy*` (including all its submodules). No other package or module in `immich_autotag*` may import anything from `immich_autotag.api.immich_proxy*`.

---

These rules must be enforced strictly, and the use of wildcards (asterisks) indicates that all submodules and files under the specified package are included in the restriction.