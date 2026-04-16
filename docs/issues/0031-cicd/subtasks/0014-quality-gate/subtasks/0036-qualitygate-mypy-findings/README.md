Title: Quality Gate (mypy) — 5 findings blocking pipeline

Summary
- Jenkins is failing the `Quality Gate (Python OO)` step during the `check_mypy` check with 5 findings. The app runs locally, but the CI Quality Gate detects typing issues that block the pipeline.

Observed errors (extracted from Jenkins log)

  1. immich_autotag/albums/album/album_user_wrapper.py:43: Argument 1 to "from_string" of "BaseUUIDWrapper" has incompatible type "UUID"; expected "str" [arg-type]
  2. immich_autotag/albums/album/album_dto_state.py:195: "AlbumResponseDto" has no attribute "assets" [attr-defined]
  3. immich_autotag/albums/album/album_dto_state.py:236: "AlbumResponseDto" has no attribute "assets" [attr-defined]
  4. immich_autotag/users/user_response_wrapper.py:64: Argument 1 to "from_string" of "BaseUUIDWrapper" has incompatible type "UUID"; expected "str" [arg-type]
  5. immich_autotag/users/user_response_wrapper.py:72: Incompatible return value type (got "str | UUID", expected "str") [return-value]

Context and notes
- The failure occurs during the `check_mypy` step invoked by `scripts/devtools/quality_gate_py/venv_launcher.sh`.
- The pipeline activates `./.venv` and runs the checks; development packages appear to be installed correctly.
- These are static type issues (mypy), not import/runtime exceptions, and originate from mismatches between used types and expected function signatures.

Files to inspect (approx. lines)
- `immich_autotag/albums/album/album_user_wrapper.py` (around line 43)
- `immich_autotag/albums/album/album_dto_state.py` (around lines 195 and 236)
- `immich_autotag/users/user_response_wrapper.py` (around lines 64 and 72)

Steps to reproduce locally (recommended)
1. Activate project venv:

```bash
source .venv/bin/activate
```

2. Run only the mypy check (from repository root):

```bash
# using the project launcher (recommended)
bash scripts/devtools/quality_gate_py/venv_launcher.sh --mode CHECK --only-check=check_mypy

# or run mypy directly (if config present):
.venv/bin/python -m mypy immich_autotag
```

3. Inspect the files and the lines reported by mypy.

Possible causes and suggested actions
- Likely cause: helper signatures (e.g. `BaseUUIDWrapper.from_string`) and actual usages don't match — for example, passing a `UUID` where a `str` is expected.
- Verify `BaseUUIDWrapper.from_string` signature (parameter type) and update callers to use `from_uuid(...)` when a `uuid.UUID` instance is available, or change the signature to accept `str | UUID` if appropriate.
- For `AlbumResponseDto.assets` — check the generated DTO/type definition: the attribute may not be present in type stubs (or may be conditional). Consider using `getattr(..., "assets", Unset)` or a targeted `# type: ignore[attr-defined]` if the attribute is only available dynamically. The more robust solution is to cast/guard the attribute access for mypy.

Temporary mitigations
- To unblock CI while fixing the root cause, you may relax the `check_mypy` gate for integration branches (not recommended long-term). Alternatively, add targeted `# type: ignore` comments for the specific lines or adjust `mypy` config to exclude the file(s).

Proposed next steps (prioritized)
1. Reproduce `check_mypy` locally and capture full output.
2. Open a PR with minimal typing fixes in the listed files (preferred) or add justified `# type: ignore` annotations.
3. Re-evaluate Quality Gate rules if false positives persist.

Attachments / logs
- Copy the selected log excerpt here (included below). Add more traces if needed.

Relevant log excerpt:

```
[CHECK] Running check_mypy …
[RUN] mypy API on immich_autotag
[FAIL] check_mypy failed: 5 findings found

  [ERROR 1] immich_autotag/albums/album/album_user_wrapper.py:43: Argument 1 to "from_string" of "BaseUUIDWrapper" has incompatible type "UUID"; expected "str" [arg-type]
  [ERROR 2] immich_autotag/albums/album/album_dto_state.py:195: "AlbumResponseDto" has no attribute "assets" [attr-defined]
  [ERROR 3] immich_autotag/albums/album/album_dto_state.py:236: "AlbumResponseDto" has no attribute "assets" [attr-defined]
  [ERROR 4] immich_autotag/users/user_response_wrapper.py:64: Argument 1 to "from_string" of "BaseUUIDWrapper" has incompatible type "UUID"; expected "str" [arg-type]
  [ERROR 5] immich_autotag/users/user_response_wrapper.py:72: Incompatible return value type (got "str | UUID", expected "str") [return-value]
```

AI Help Prompt (to provide to another assistant)

Context summary:
- Jenkins runs `check_mypy` and fails with 5 findings listed above. The app runs locally and the venv is correct.
- Affected files: `immich_autotag/albums/album/album_user_wrapper.py`, `immich_autotag/albums/album/album_dto_state.py`, `immich_autotag/users/user_response_wrapper.py`.

Questions for the assistant:
1. What is the most likely cause for each mypy error listed?
2. Propose concrete typing fixes (change signature, explicit conversion, or `| UUID` / `# type: ignore`) with code snippets.
3. Note the risks of each fix and suggest less invasive alternatives if applicable.
4. Provide exact commands to reproduce the same mypy run as in CI (including flags and suggested mypy version).

Files & lines to include in context when asking for help:
- immich_autotag/albums/album/album_user_wrapper.py (approx line 43)
- immich_autotag/albums/album/album_dto_state.py (approx lines 195, 236)
- immich_autotag/users/user_response_wrapper.py (approx lines 64, 72)

Expected output from the assistant:
- Diagnosis per error (1–5) with the implicated line and a short explanation.
- Suggested patch per error (unified patch or snippet) ready for PR.
- Exact command to run mypy and verify the fix.

Assignment
- Leave unassigned; assign to the CI/mypy triage owner or a person familiar with the `albums`/`users` submodule.

Notes
- If you confirm, I can: (A) create a PR with the minimal typing fixes proposed, or (B) add instrumentation to the Jenkins job to collect more info (for example, `mypy --version`, `which python`, and the full mypy output`).