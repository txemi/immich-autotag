# Profiling CI integration (Jenkins)

This document describes how to run profiling in Jenkins using the existing profiling helpers.

Files
- `profile_run.sh`: existing cProfile wrapper (creates `profile.stats`).
- `run_profile_jenkins.sh`: this wrapper sets up the venv, activates it and runs `profile_run.sh`, placing artifacts in `profiling_artifacts/`.

Quick Jenkins snippet (add a stage):

```groovy
stage('Profiling (optional)') {
  when { environment name: 'RUN_PROFILING', value: '1' }
  steps {
    sh 'chmod +x scripts/devtools/profiling/run_profile_jenkins.sh'
    sh 'bash scripts/devtools/profiling/run_profile_jenkins.sh -- --sample-arg'
    archiveArtifacts artifacts: 'profiling_artifacts/**', allowEmptyArchive: false
  }
}
```

Notes
- This approach reuses the proven `profile_run.sh` and keeps profiling tools together under `scripts/devtools/profiling/`.
- Consider adding `py-spy` or `pyinstrument` in the future to generate flamegraphs directly.
