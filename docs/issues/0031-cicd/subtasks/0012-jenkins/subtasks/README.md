# Jenkins Retention Strategies - Subtasks

## Quick Choice

**Do you have disk space problems RIGHT NOW?**
- **YES** → Go to [001](001-jenkins-build-retention-groovy-script/) (quick cleanup)
- **NO** → Go to [002](002-jenkins-retention-pipeline-plugins-analysis/) (prevent future)
- **NOT SURE** → Start with 001, then implement 002

---

## Subtask 001: Groovy Script Cleanup

### When to use:
- You need immediate disk space relief
- You have existing accumulation problems
- You want to avoid plugin dependencies
- You want to test with dry-run mode first

### What you get:
- Generic script working on any Jenkins
- Delete old builds, remove orphaned workspaces
- Dry-run mode to preview before deleting
- Can schedule for monthly maintenance
- No plugin dependencies required

### Files:
- `README.md` - Complete usage guide
- `jenkins_cleanup_old_builds.groovy` - Ready-to-use script

### Quick flow:
1. Copy script to Jenkins Script Console
2. Set dryRun = true and run (preview mode)
3. If satisfied, set dryRun = false and run (execute)
4. Schedule monthly via Scriptler or Pipeline job

**[→ Go to Subtask 001](001-jenkins-build-retention-groovy-script/)**

---

## Subtask 002: Pipeline & Plugins Analysis

### When to use:
- You want to prevent future accumulation
- You can modify your Jenkinsfile
- You want automatic per-build cleanup
- You have access to install plugins

### What you get:
- Analysis of buildDiscarder in Jenkinsfile
- Plugin recommendations (Workspace Cleanup Plugin)
- Configuration examples
- Comparison of retention strategies
- Decision history from January 2026

### Implementation example:
```groovy
options {
    buildDiscarder(logRotator(
        numToKeepStr: '4',           // Keep 4 builds
        artifactNumToKeepStr: '2'    // Keep 2 with artifacts
    ))
}

post {
    always {
        cleanWs()  // Requires Workspace Cleanup Plugin
    }
}
```

### Advantages:
- Automatic execution (no manual runs)
- Prevents accumulation from start
- Version-controlled in Jenkinsfile
- Works per-job or globally

**[→ Go to Subtask 002](002-jenkins-retention-pipeline-plugins-analysis/)**

---

## Both Together = Complete Solution

**Recommended workflow:**

```
Phase 1: Quick Win (Days 1-2)
└─ Run Groovy script (001) to free up disk space immediately

Phase 2: Long-term Prevention (Week 1)
└─ Implement Pipeline/Plugins (002) to prevent re-accumulation

Phase 3: Maintenance (Week 2+)
└─ Schedule Groovy script monthly as safety net
```

Why both?
- **Groovy script** (001) = Emergency cleanup for existing problems
- **Pipeline/Plugins** (002) = Prevention so you don't have the problem again
- They're complementary, not competing solutions

---

## Decision Matrix

| Scenario | Start with | Then | Result |
|----------|-----------|------|--------|
| Have disk problems now | 001 | 002 | Immediate relief + prevention |
| No problems yet | 002 | (optional 001) | Prevent problems from start |
| Unsure | 001 | 002 | Safe to do both |

---

## Related Context

- **Parent:** [0031-cicd: CI/CD Infrastructure](../../)
- **Related:** [0014-jenkins-pipeline-containerization](../../../0014-jenkins-pipeline-containerization/)
- **Related:** [0022-release-preparation](../../../0022-release-preparation/)

---

## Next Steps

**Choose your path:**

1. [001: Groovy Script](001-jenkins-build-retention-groovy-script/) - Immediate cleanup
2. [002: Pipeline & Plugins](002-jenkins-retention-pipeline-plugins-analysis/) - Sustainable prevention