# Issue Tracking & Design System

This directory is the core of the project's task management, issues, and design decisions. We use a **Local-first** and **Documentation-as-Code** approach to ensure that the technical context is eternal and processable by AI.

## 📚 Standards and Conventions
To avoid "reinventing the wheel", this system is based on the following industry standards:
## 📚 Standards and Conventions
To avoid "reinventing the wheel", this system is based on the following industry standards:

1.  **[ADR (Architecture Decision Records)](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions):** We follow Michael Nygard's pattern to record technical decisions in a numbered and chronological way.
2.  **[RFC (Request for Comments)](https://github.com/rust-lang/rfcs):** We adopt the workflow of projects like Rust or React, where significant changes are proposed and documented before being implemented.
3.  **[Documentation-as-Code](https://www.writethedocs.org/guide/documentation-as-code/):** We treat documentation with the same rigor as source code (versioned in Git, peer review, and Markdown format).

## 🛠 System Structure
Each task or "issue" resides in its own numbered folder (`XXXX-slug`):
## 🛠 System Structure
Each task or "issue" resides in its own numbered folder (`XXXX-slug`):

- **`index.md`**: The issue's master document. Contains requirements, tech stack (AWS, AI/ML, C++, Python, etc.) and acceptance criteria.
- **`ai-context.md`**: Critical record of LLM interaction. Prompts and reasoning are saved here so that AI-generated knowledge is not lost.
- **`design/`**: Directory for schemas, architecture diagrams (Mermaid/Draw.io) and detailed technical proposals.

## 🚀 AI Workflow (Copilot/Cursor)
To maintain consistency and avoid duplicate IDs, always use this command with your AI assistant:

> *"Based on this directory's protocol, create a new issue for [brief description]. Increment the ID based on the last existing one and update the `registry.md`."*

---
*This system ensures that the project's knowledge is sovereign, does not depend on external SaaS tools, and is optimized for analysis by language models.*

## ⚠️ Performance Regression: Test Suite Duration

Brief description: until recently the complete test suite took ~4 hours and today it takes ~14 hours — an unacceptable increase that needs to be investigated.

Initial clues:
- The **auto-album creation** feature might have generated a large number of new albums, which possibly impacts steps that iterate over albums or repeatedly query metadata.
- Another possibility is that some part of the code is doing redundant work (repeated calls, recalculations, unexpected O(N^2) operations, or unnecessary I/O accesses within loops).

Proposed strategy:
- Automate profiling generation from CI to capture reproducible samples (CPU, wall times, memory usage, flamegraphs). See [issue 0021 — Profiling & Performance Reports](../docs/issues/0021-profiling-performance/).
- Start with a small representative sample to keep CI time reasonable and then scale locally for larger reproductions.
- Analyze profiles to identify hotspots and repeated calls; prioritize changes that reduce rework (caching, avoid repeated I/O, limit album scanning).

Immediate actions:
1. Integrate a small profiling job in CI that runs a representative set of tasks and archives the artifacts (CPU/memory profiles, flamegraphs).
2. Provide scripts in `scripts/profiling/` and a `README` with instructions to run locally and in CI.
3. Review critical paths that operate on albums and classification to search for repeated operations or costly queries.

If you want, I can create the example `scripts/profiling/run_profile.sh` and add a minimal job for GitHub Actions or Jenkins that archives the artifacts.