# Issue System Conventions

Guidelines for creating and maintaining issues under `docs/issues/`.
These apply to **new work going forward**; existing structure is not required to comply immediately.

## Mandatory artifacts (per issue)

| Artifact | Location | Rule |
|---|---|---|
| `README.md` | `docs/issues/<issue>/README.md` | Required. Index of what exists; no invented statuses. |
| Entry in `registry.md` | `docs/issues/registry.md` | Required. Add when creating or relocating an issue. |

## Optional artifacts

- `ai-context.md` — AI context summary at the issue level. Include a `Last verified:` date so staleness is visible.
- Subtask folders with free-form content (no README required inside subtasks).

## Naming

- Always `README.md` (uppercase). Not `readme.md`, not `index.md`, not `INDEX.md`.
- Subtask folders: `NNN-short-description/` (zero-padded number + kebab-case).

## Nesting

Nest when content is genuinely subordinate or tightly coupled to its parent. Depth is not a problem in itself.
Create a new issue (and register it) when a subtask grows large enough to be tracked independently.

## ai-context.md usage

- One file per issue, at the issue root (not inside subtask folders).
- Always include a `Last verified: YYYY-MM-DD` line at the top.
- Update the date whenever you read and confirm the context is still accurate.
- Describes the current state, not future plans.

## Registry maintenance

- Update `registry.md` when: creating an issue, relocating an issue (fix the link), or closing one.
- Update `Last updated` date on every registry edit.
- If an issue is absorbed into another, update its link to the new location rather than deleting the row.

## The "touch it, improve it" rule

When editing any file in `docs/issues/` for another reason, take the opportunity to:
- Verify the issue README reflects what actually exists.
- Update `Last verified` in `ai-context.md` if you read it.
- Fix any broken links in `registry.md`.

No need to reorganize anything proactively.

---

*Last updated: 2026-04-24*
