# 1. Contributing to Immich AutoTag

Thank you for your interest in contributing to Immich AutoTag! This project is developed in spare time and all contributions are welcome.

## 1.1. How to Contribute
- **Bug fixes, documentation improvements, and feature suggestions** are always appreciated.
- If you have ideas for new features, improvements, or want to help with code, feel free to open a pull request or issue.



## 1.2. Style rules for humans and language models

### 1.2.1. Attribute access in typed classes

- **Do NOT use `getattr` or `hasattr` to access known attributes in models, dataclasses, or classes with `__slots__`.**
- Always access attributes directly (`obj.attribute`).
- Rationale: direct access is safer, more predictable, and works better with static analysis and refactoring tools. Introspection (`getattr`, `hasattr`) is only allowed for truly dynamic cases (e.g., migrations, generic serialization, or frameworks that explicitly require it).
- This rule applies to both humans and language models/AI. Code should be as predictable and robust as in Java or other statically typed languages.

Incorrect example:

```python
value = getattr(user, 'name', None)  # ❌ Not allowed if 'name' is a declared attribute
```

Correct example:

```python
value = user.name  # ✅ Always preferred
```

If in doubt, ask before using introspection.

### 1.2.2. Models and class types (project conventions)

- **Do NOT use Python `@dataclass` for new models or DTOs in this project.**
- **Use `pydantic` models** (e.g. `pydantic.BaseModel`) for classes that are serialized, used as DTOs, or exchanged with external services (HTTP APIs, clients). Pydantic gives explicit validation, parsing, and consistent serialization behavior.
- **Use `attrs`** (`attrs.define` / `attrs.dataclass` style) for internal/domain classes that contain logic, mutability rules, or non-trivial behaviour and are not intended primarily for direct serialization. `attrs` provides concise declarations and good runtime performance while integrating well with existing code patterns.

Rationale:
- `pydantic` → best for serialization & validation (external-facing contracts).
- `attrs` → best for internal domain objects with behaviour.
- `dataclasses` are intentionally avoided to keep a single, explicit approach for serializable models (`pydantic`) and for logic/domain classes (`attrs`). This helps static analysis, consistent validation, and predictable serialization across the codebase.

Examples:

Correct (serializable DTO):

```py
from pydantic import BaseModel

class AssetDto(BaseModel):
	id: str
	filename: str

```

Correct (internal/domain class):

```py
import attrs

@attrs.define(auto_attribs=True)
class Album:
	id: str
	name: str

	def rename(self, new_name: str) -> None:
		self.name = new_name
```

Incorrect:

```py
from dataclasses import dataclass

@dataclass
class Model:
	id: str
	name: str
```

If you need to interoperate between `attrs` classes and `pydantic` (e.g., an internal class that must be serialized), convert explicitly in a well-tested adapter layer and prefer `pydantic` for the external contract.


### 1.2.3. Tuple returns and typed return objects

- **Do NOT return plain tuples from functions as a way to return multiple values.** Tuples are ambiguous and hinder static analysis and discoverability.
- Instead, return a small typed object: a `pydantic` model if the value is a DTO/serializable, or an `attrs` class for internal value objects. Where backward compatibility is required, prefer wrapper objects that implement `__iter__` to allow tuple-like unpacking temporarily while callers are migrated.

Tooling:
- The repository includes an AST-based checker (`scripts/devtools/check_no_tuples.py`) that enforces this policy in CI. It will flag:
  - functions that `return` tuple literals
  - return annotations using `typing.Tuple` or `tuple`
  - class-level attributes assigned tuple literals
  - `self.attr = (...)` tuple assignments in `__init__`
- There's also a codemod (`scripts/devtools/fix_tuples.py`) that can apply simple, safe transformations (creates small typed result classes and replaces tuple returns) — use with care and review changes.

If you are unsure which type to pick for a specific case, open an issue or ask on the PR for guidance.

## 1.3. Branch Policy

Starting from this version, we enforce a **branching strategy** to maintain code quality and stability:

### 1.3.1. Branch Structure
- **`main`**: Production-ready code. All code merged here must come from `develop` branch via Pull Request.
- **`develop`**: Integration branch for features. This is where continuous integration and testing happens.
- **`feature/*`**: Feature branches created from `develop` for individual work items.

### 1.3.2. Workflow
1. Create a feature branch from `develop`: `git checkout -b feature/your-feature develop`
2. Make your changes and test locally
3. Submit a Pull Request to `develop` (not directly to `main`)
4. After review and tests pass, merge to `develop`
5. Periodically, tested and validated code from `develop` is merged to `main`

### 1.3.3. Quality Gates (Future)
We are working on implementing automated quality gates including:
- Full test suite execution
- Large-scale photo batch processing validation
- Code quality checks

Once these are in place, they will be enforced before any merge to `main`. **Until then, `develop` is our integration branch where we prepare code for production.**

## 1.4. Guidelines
- Please follow the existing code style and structure as much as possible.
- For major changes, open an issue first to discuss what you would like to change.
- Make sure to test your changes before submitting a pull request.
- **Always target `develop` branch with your PRs, not `main`** (except for critical hotfixes, which require discussion first)

## 1.5. Getting Started
- See the [Developer Guide](./development.md) for technical details and project structure.
- If you have questions, open an issue or start a discussion on GitHub.

## 1.6. Publishing
- The publication of the Python library to public repositories works when using the local scripts.
- However, automated publishing via GitHub Actions is not yet functional. Any help with enabling or fixing this CI/CD workflow would be especially valuable!

---

*Any help is appreciated. This is a community-driven project and your contributions make it better!*
