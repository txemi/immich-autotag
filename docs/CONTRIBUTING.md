# Contributing to Immich AutoTag

Thank you for your interest in contributing to Immich AutoTag! This project is developed in spare time and all contributions are welcome.

## How to Contribute
- **Bug fixes, documentation improvements, and feature suggestions** are always appreciated.
- If you have ideas for new features, improvements, or want to help with code, feel free to open a pull request or issue.

## Branch Policy

Starting from this version, we enforce a **branching strategy** to maintain code quality and stability:

### Branch Structure
- **`main`**: Production-ready code. All code merged here must come from `develop` branch via Pull Request.
- **`develop`**: Integration branch for features. This is where continuous integration and testing happens.
- **`feature/*`**: Feature branches created from `develop` for individual work items.

### Workflow
1. Create a feature branch from `develop`: `git checkout -b feature/your-feature develop`
2. Make your changes and test locally
3. Submit a Pull Request to `develop` (not directly to `main`)
4. After review and tests pass, merge to `develop`
5. Periodically, tested and validated code from `develop` is merged to `main`

### Quality Gates (Future)
We are working on implementing automated quality gates including:
- Full test suite execution
- Large-scale photo batch processing validation
- Code quality checks

Once these are in place, they will be enforced before any merge to `main`. **Until then, `develop` is our integration branch where we prepare code for production.**

## Guidelines
- Please follow the existing code style and structure as much as possible.
- For major changes, open an issue first to discuss what you would like to change.
- Make sure to test your changes before submitting a pull request.
- **Always target `develop` branch with your PRs, not `main`** (except for critical hotfixes, which require discussion first)

## Getting Started
- See the [Developer Guide](./development.md) for technical details and project structure.
- If you have questions, open an issue or start a discussion on GitHub.

## Publishing
- The publication of the Python library to public repositories works when using the local scripts.
- However, automated publishing via GitHub Actions is not yet functional. Any help with enabling or fixing this CI/CD workflow would be especially valuable!

---

*Any help is appreciated. This is a community-driven project and your contributions make it better!*
