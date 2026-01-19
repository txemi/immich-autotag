"""
Package: albums

Responsibilities:
    - Core logic and abstractions for albums (wrappers, collection, CRUD, policies).
    - Does NOT contain asset-specific business logic or assignment logic.

Dependencies:
    - This package MUST NOT depend on 'assets' or any asset business logic.
    - It can be freely used by other modules for generic album manipulation.

Notes:
    - If you need asset-album relationship logic, use 'assets/albums/'.
"""
