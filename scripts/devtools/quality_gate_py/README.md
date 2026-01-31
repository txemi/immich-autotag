# Python QualityGate

Python QualityGate is a modular, extensible tool designed to enforce code quality standards in Python projects. Inspired by CI/CD quality gates, it provides a unified framework to run static analysis, formatting, linting, and custom policy checks in a configurable and pluggable way.

## Purpose
The main goal of Python QualityGate is to help teams and individual developers maintain high code quality and consistency across their Python codebases. It automates the execution of multiple quality checks (such as mypy, ruff, flake8, black, isort, and custom rules) and can be easily integrated into CI pipelines or used locally.

## Key Features
- Modular check system: add, remove, or customize checks as needed
- Extensible: implement your own checks using a simple base class (with attrs support)
- Designed for both CI/CD and local development workflows
- Clear, actionable output and fail-fast behavior for blocking issues
- All checks and core classes use `attrs` for robust, type-safe data modeling

## Structure
- `python_qualitygate/` — Main package
- `python_qualitygate/implementations/` — Built-in and reference check implementations
- All classes use `attrs` for data modeling (supports inheritance)

## Getting Started
1. Install dependencies: `pip install -r requirements.txt`
2. Use the CLI or import as a library in your own tools

---
This project is under active development. Contributions and suggestions are welcome!
