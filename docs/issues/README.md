# Issue Tracking & Design System

This directory is the core of the project's task management, issues, and design decisions. We use a **Local-first** and **Documentation-as-Code** approach to ensure that the technical context is eternal and processable by AI.

## 📚 Standards and Conventions

To avoid "reinventing the wheel", this system is based on the following industry standards:

1.  **[ADR (Architecture Decision Records)](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions):** We follow Michael Nygard's pattern to record technical decisions in a numbered and chronological way.
2.  **[RFC (Request for Comments)](https://github.com/rust-lang/rfcs):** We adopt the workflow of projects like Rust or React, where significant changes are proposed and documented before being implemented.
3.  **[Documentation-as-Code](https://www.writethedocs.org/guide/documentation-as-code/):** We treat documentation with the same rigor as source code (versioned in Git, peer review, and Markdown format).

## 🛠 Issue Structure

Each issue resides in its own numbered folder (`00XX-slug`):

- **`README.md`**: Master document for the issue. Contains context, goals, and status.
- **`subtasks/`**: Subfolder for related subtasks, each with its own folder and `README.md`
- **`design/`**: Optional directory for architecture diagrams, schemas, and technical proposals (Mermaid/Draw.io)
- **`ai-context.md`**: Optional record of LLM interactions and reasoning (when relevant)

## Naming Conventions

- Use **descriptive, specific slugs** (e.g., `jenkins-build-retention-groovy-script`, `public-registry-cleanup-and-user-validation`)
- Avoid generic or outdated names
- Subtasks are **numbered** (e.g., `001-initial-implementation`) for clarity and version tracking

## Current Issue Categories

| Category | Issues | Purpose |
|----------|--------|---------|
| **Features** | 0024-0027, 0030, 0032 | Application features (albums, assets, config, rules, user management) |
| **DevOps/Infrastructure** | 0021-0022, 0031 | Deployment, performance, CI/CD |
| **Development Workflow** | 0020 | Git workflows, documentation tracking, branching strategy |
| **Management** | 0028, 0033 | Project management, community engagement |
| **Core Logic** | 0029 | Core system logic and architecture |

## Best Practices

- Keep issues focused; split broad topics into **subtasks**
- Update `README.md` files to reflect current structure and cross-links
- Use tables for major reorganizations or categorizations
- Document rationale for significant changes
- Reference related issues via links (e.g., `[0020-docs-track-branch](../0020-docs-track-branch/)`)

## Registry

See [`registry.md`](./registry.md) for a complete list of active issues with status and version information.

---

*Last updated: 2026-02-01*