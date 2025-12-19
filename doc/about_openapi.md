# About OpenAPI Client Generation for Immich AutoTag

This document explains how the Python client library for Immich is generated and maintained in this project.

> Note: All scripts in this folder use the standard virtual environment `.venv/` at the project root. Activate it before installing dependencies or running examples.

## Project Evolution
- Started with bash and curl scripts to test endpoints.
- Progressed to simple Python scripts using `requests`.
- Now uses an auto-generated Python client from the official Immich OpenAPI spec, which is the foundation of this folder.

## How is the client generated?

This folder contains:
- The `immich-client/` subfolder, generated automatically from the official Immich OpenAPI spec.
- Examples and utilities that use the generated client for robust, type-safe API access.

### Steps to generate the client

1. Install the generator in your virtual environment:
    ```bash
    pip install openapi-python-client
    ```
2. Generate the client library:
    ```bash
    openapi-python-client generate --url https://raw.githubusercontent.com/immich-app/immich/main/open-api/immich-openapi-specs.json
    ```
    This will create the `immich-client/` folder with all necessary code.
3. Install the client in editable mode:
    ```bash
    pip install -e immich-client
    ```

## Organization
- Example scripts show how to import and use the generated client to interact with the Immich API.
- This approach is recommended for maintainable, scalable, and type-checked development.

See the `immich-client/README.md` and the example scripts for more details.

> Updated: December 19, 2025
