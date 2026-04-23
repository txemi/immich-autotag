Run the Python Quality Gate for immich-autotag and summarise the result.

## Steps

1. Run the quality gate:
   ```
   bash scripts/devtools/quality_gate_py/venv_launcher.sh --level=STANDARD --mode=CHECK
   ```

2. Report the outcome clearly:
   - If it passes: confirm all checks passed and the gate is green.
   - If it fails: list exactly which checks failed and show the relevant error lines (not the full stack trace unless asked). Suggest a fix if the cause is obvious (e.g. a ruff formatting issue → `ruff format .`; a mypy error → show the offending line).

3. Do not re-run automatically after a failure — wait for the user to fix the issue and ask to re-run.
