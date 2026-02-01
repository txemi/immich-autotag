# Jenkins Build and Workspace Retention

## Problem

In multi-branch Jenkins setups, accumulated builds and orphaned workspaces consume significant disk space. Default retention policies don't always apply correctly, leading to:

- Old builds accumulating in every branch/PR job
- Orphaned workspaces persisting after jobs are deleted  
- Disk space filling up quickly with large artifacts
- Jenkins performance degrading

## Solution Approaches

### Approach 1: Groovy Script (Immediate Relief)
- Location: `001-jenkins-build-retention-groovy-script/`
- For existing disk space problems
- Works without plugin dependencies
- Manual or scheduled execution

### Approach 2: Pipeline/Plugins (Prevention)
- Location: `002-jenkins-retention-pipeline-plugins-analysis/`
- For preventing future accumulation
- Declarative retention in Jenkinsfile
- Automatic per-build cleanup

## Recommended: Use Both

1. **Quick win:** Run Groovy script for immediate cleanup
2. **Going forward:** Implement Pipeline/Plugins to prevent re-accumulation
3. **Maintenance:** Schedule Groovy script monthly as fallback

## Navigation

See [subtasks/](subtasks/) for detailed implementations of both approaches.