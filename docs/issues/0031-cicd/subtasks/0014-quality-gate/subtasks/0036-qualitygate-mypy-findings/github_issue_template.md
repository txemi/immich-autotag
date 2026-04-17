Title: CI: mypy failures due to immich-client DTO changes (assets/id)

Body

Summary
- The Jenkins Quality Gate `check_mypy` is failing with typing errors that appear to be caused by changes or discrepancies in the `immich-client` generated DTOs. These failures block CI for branch `fix/immich-client-dto-compat` and may be caused by the server/client changing the shape/types of Album/User DTOs (notably `id` and `assets`).

Why this matters
- The failures result in runtime AttributeError in production workflows (see backtrace) and prevent CI from passing. We need a coordinated investigation because the fix may require updating wrappers, adding robust adapters, or clarifying contract expectations between client and server.

Branch and related artifacts
- Branch created for investigation and minimal fixes: `fix/immich-client-dto-compat`
- LLM-ready analysis and logs: docs/issues/0031-cicd/subtasks/0014-quality-gate/subtasks/0036-qualitygate-mypy-findings/
  - analysis_llm_report.md
  - mypy_findings.md
  - backtrace.md
  - README.md

Observed CI findings (summary)
- mypy reported 5 errors (see attached `mypy_findings.md`). Examples:
  - `BaseUUIDWrapper.from_string` called with `UUID` (expected `str`).
  - `AlbumResponseDto` may not include `assets` in some DTO versions causing AttributeError at runtime.

Full reproduction steps
1. Checkout branch: `git fetch && git checkout fix/immich-client-dto-compat`
2. Create and activate venv per repository instructions:

```bash
source .venv/bin/activate
```

3. Run the CI mypy check used by Jenkins:

```bash
bash scripts/devtools/quality_gate_py/venv_launcher.sh --mode CHECK --only-check=check_mypy
# or
.venv/bin/python -m mypy immich_autotag
```

Attached logs & evidence
- See `mypy_findings.md` and `backtrace.md` in the same folder. The backtrace shows runtime AttributeError: 'AlbumResponseDto' object has no attribute 'assets'.

What we tried (minimal, non-invasive changes)
- Convert values passed to `BaseUUIDWrapper.from_string` using `str(uid)` when the value might be a `UUID`.
- Use `getattr(dto, "assets", UNSET|None)` before iterating `assets` to avoid attribute errors and make runtime checks explicit.

Requested investigation
1. Confirm whether `immich-client` or Immich server releases changed DTO types/fields recently (focus: `AlbumResponseDto.assets`, user `id` types). Provide exact versions/releases and diffs if found.
2. Determine whether the correct long-term fix is to:
   - adapt wrappers to be robust across DTO versions (recommended), or
   - pin `immich-client` to a specific version and enforce API contract, or
   - update code generation to include missing fields in stubs.
3. Produce minimal, tested patches (diffs) and unit tests that cover both partial (search) and full (detail) DTOs.

Suggested labels
- bug, ci, mypy, needs-investigation, high-priority

Suggested assignees
- `@maintainers`, `@owners` of albums/users modules, and the CI/mypy triage owner.

Checklist (for the issue)
- [ ] Confirm `immich-client` version in CI and local environments
- [ ] Produce exact diffs showing DTO changes (if any)
- [ ] Implement robust wrapper/adapters or update stubs
- [ ] Add unit tests covering partial vs full DTOs
- [ ] Run `check_mypy` and verify CI passes
- [ ] Merge PR and monitor production runs

Notes for LLM collaborators
- The folder contains an LLM-oriented report (`analysis_llm_report.md`) which includes mypy output and runtime backtraces. If you are a model analyzing this, please: (A) look for changes in `immich-client` releases; (B) propose minimal patches that keep runtime safety and typing correctness; (C) generate unit tests simulating DTO variations.

Next actions (propose)
- If you want, I can open the GitHub issue with the title/body above and tag suggested assignees; confirm and I will create it.
