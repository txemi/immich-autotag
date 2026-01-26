# Release Preparation Checklist

## Main Tasks

- [ ] Review the general documentation
- [ ] Review that the configuration is documented
- [ ] Update the CHANGELOG.md
- [ ] Review the internal configuration (ensure we are not in debug mode)
- [ ] Revisar la seguridad del workflow de release en GitHub Actions ([ver subtask](subtasks/github-actions-release-safety.md))
- [ ] Revisar y refactorizar la lógica cableada de la raíz del proyecto en `immich_autotag/run_output/manager.py` (función `get_run_output_dir`).
      - Actualmente la ruta se calcula de forma rígida; debe ser flexible y revisada antes de la release.

## Notes
- Add subtasks in the `subtasks` folder if you need to break down any task.
