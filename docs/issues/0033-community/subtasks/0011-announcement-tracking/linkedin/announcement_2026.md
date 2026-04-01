Immich AutoTag: Major New Release – Instantly Organize and Classify Your Photo Library

I'm excited to announce a major new release of Immich AutoTag, an open-source tool designed to help you automatically organize, classify, and maintain large photo and video libraries with minimal effort.

Key highlights of this release:

• 🚀 Instant CLI from PyPI: Run Immich AutoTag instantly with `pipx run immich-autotag` – no manual setup required.
• 🏷️ Advanced Tagging & Album Logic: Automatically classifies assets based on albums, tags, and duplicates.
• 🕒 Automatic Date Repair: Detects and fixes incorrect or missing dates for your assets using filenames and duplicate analysis.
• 🗃️ Auto-Album Creation: Converts your old folder structures into albums in Immich.
• ⚠️ Conflict & Unclassified Detection: Instantly highlights assets that need your attention or have conflicting classifications.
• 🛠️ Flexible Configuration: Supports both YAML and Python config files, with self-documented templates for easy customization.
• 📊 Detailed Logs & Statistics: Tracks your progress and helps you maintain a clean, organized library.
• 🐳 (Experimental) Docker Support: Early Docker image available for testing.

Why Immich AutoTag?
- Save hours (or days) organizing large, messy photo collections.
- Instantly identify and resolve unclassified or conflicting assets.
- Automate repetitive tagging and album management tasks.
- Keep your photo dates accurate and consistent, even after years of device changes and imports.

Learn more and get started:
- Quick Start: https://github.com/txemi/immich-autotag#quick-start
- Full changelog: https://github.com/txemi/immich-autotag/blob/main/CHANGELOG.md
- Simple explanation: https://github.com/txemi/immich-autotag/blob/main/docs/explain-like-im-5.md

Feedback and collaboration are welcome! If you have questions or suggestions, feel free to connect or open an issue on GitHub.

#OpenSource #PhotoManagement #Automation #Python #Immich #Productivity

---

## v0.80.0 — 2026-03-31

Immich AutoTag v0.80.0: User Groups, Smarter Rule Engine & Production-Ready Continuous Mode

I'm excited to share v0.80.0 of Immich AutoTag — a major milestone release that consolidates months of work and marks the beginning of our stabilization roadmap toward v1.0.0.

Key highlights:

• 👥 User Permissions & Groups: Automatic access control for albums based on configurable user group rules — tested with 500+ albums.
• 🔁 Continuous Batch Mode: Fully stable long-running mode that processes new assets automatically without restarts.
• 🧩 Enhanced Rule Engine: Now supports both regex and simplified patterns for flexible, powerful asset classification.
• 🗂️ Duplicate Album Recovery: Safely resolves same-name album conflicts with cleanup and rename strategies.
• ✅ Checkpoint Resume: Stable and enabled by default — resume from where you left off after any interruption.
• 🗃️ Auto Album Creation from Folders: Stable and enabled by default.
• ⚙️ Configurable Execution Phases: Toggle processing phases independently for fine-grained control.
• 🔧 API Architecture Refactor: Cleaner modular structure for better long-term maintainability.

⚠️ Note: The Docker image has a known issue in some environments (DNS instability). Recommended workaround: use pipx (`pipx run immich-autotag`). Full tracking at GitHub Issue #43.

Get started: https://github.com/txemi/immich-autotag#quick-start
Full changelog: https://github.com/txemi/immich-autotag/blob/main/CHANGELOG.md
ELI5 explanation: https://github.com/txemi/immich-autotag/blob/main/docs/explain-like-im-5.md

Feedback and collaboration always welcome!

#OpenSource #PhotoManagement #Automation #Python #Immich #Productivity #SelfHosted

<!-- STATUS: draft — not yet posted -->
