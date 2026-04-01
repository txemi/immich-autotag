[Showcase] Immich AutoTag – New: Instant CLI, Auto-Album Creation, Auto Date Fix, Smart Tagging & More!

Hi everyone! I’m excited to share a major new release of Immich AutoTag, the open-source tool for automatic photo and video classification and tagging in Immich.

What’s new and improved in this release?

- 🚀 Instant CLI from PyPI: Run Immich AutoTag instantly with `pipx run immich-autotag` – no manual setup or environment creation required.
- 📝 Quick Start & User-Focused Docs: Clear, user-friendly documentation and a streamlined Quick Start guide.
- 🛠️ Flexible Configuration: Now supports both YAML and Python config files, with self-documented templates for easy customization.
- 🏷️ Advanced Tagging & Album Logic: Automatic classification based on albums, tags, and duplicates.
- 🕒 Automatic Date Repair: Detects and fixes incorrect or missing dates for your assets based on filenames and duplicate analysis.
- ⚠️ Conflict Detection: Instantly highlights assets with conflicting classifications, so you can resolve issues quickly.
- ❓ Unclassified Asset Detection: Easily find which photos or videos remain unorganized or unclassified.
- 🔄 Continuous Tagging Script: New loop script for continuous asset tagging/classification during heavy editing sessions.
- 📊 Detailed Logs & Statistics: Automatic generation of modification reports and statistics for tracking your library’s organization.
- 🗂️ Exclude Assets by Web Link: Easily exclude specific assets from processing.
- 🗃️ Automatic Album Creation from Folders: Now stable and enabled by default!
- 🐳 (Experimental) Docker Support: Early Docker image available for testing (not yet officially documented).

Why use Immich AutoTag?
- Save hours organizing large photo libraries.
- Instantly detect unclassified or conflicting assets.
- Automate repetitive tagging and album management tasks.
- Keep your photo dates accurate and consistent.

Get Started
- See the [README](https://github.com/txemi/immich-autotag#quick-start) for instant setup instructions.
- Full changelog: [CHANGELOG.md](https://github.com/txemi/immich-autotag/blob/main/CHANGELOG.md)

Feedback & Support
- Questions, issues, or feature requests? Open a ticket on [GitHub Issues](https://github.com/txemi/immich-autotag/issues).

Previous Reddit discussion: https://www.reddit.com/r/immich/comments/1pse1qk/comment/nvcmpf0/

For a super simple, non-technical explanation of what Immich AutoTag does, see: [Explain Like I'm 5 (ELI5)](https://github.com/txemi/immich-autotag/blob/main/docs/explain-like-im-5.md)

Thank you for your support and feedback!

---

## v0.80.0 — 2026-03-31

[Showcase] Immich AutoTag v0.80.0 – User Groups, Smarter Rule Engine, Continuous Batch Mode & More!

Hi everyone! I'm excited to share the v0.80.0 release of Immich AutoTag — a major milestone release that consolidates months of development across user permissions, rule engine improvements, and production-grade stability.

What's new in v0.80.0?

- 👥 User Permissions & Groups: Automatic assignment of permissions to users based on rules; creation and management of user groups for advanced access control; full synchronization system now consolidated and stable.
- 🔁 Continuous Batch Mode: The tool now runs continuously and automatically processes new assets as they arrive — no manual restarts needed.
- 🧩 Enhanced Rule Engine: Now supports both regex patterns and simplified common-use patterns for more flexible and powerful classification.
- 🗂️ Duplicate Album-Name Recovery: New flow with cleanup and rename strategies to resolve same-name album conflicts safely.
- ⚙️ Configurable Execution Phases: Toggle key processing phases independently (album assignment, classification validation, duplicate-tag analysis, album-date consistency, tag conversions).
- 🏥 Automatic Temporary Album Cleanup: Detects and removes unhealthy temporary albums.
- ✅ Checkpoint Resume: Now stable and enabled by default — resume processing from the last processed asset after any interruption.
- 🗃️ Auto Album Creation from Folders: Stable and enabled by default.
- 🔧 API Architecture Refactor: Modular entrypoints (albums/assets/tags/users/server) for better maintainability.

⚠️ Known issue (Docker): In some environments, the Docker image may fail to access the Immich API. Workaround: use the pipx method (`pipx run immich-autotag`). Tracked in [GitHub Issue #43](https://github.com/txemi/immich-autotag/issues/43).

Get Started
- See the [README](https://github.com/txemi/immich-autotag#quick-start) for instant setup instructions.
- Full changelog: [CHANGELOG.md](https://github.com/txemi/immich-autotag/blob/main/CHANGELOG.md)
- ELI5 explanation: [Explain Like I'm 5](https://github.com/txemi/immich-autotag/blob/main/docs/explain-like-im-5.md)

Feedback & Support
- Questions, issues, or feature requests? Open a ticket on [GitHub Issues](https://github.com/txemi/immich-autotag/issues).

Thank you for your continued support and feedback!

<!-- STATUS: draft — not yet posted -->
