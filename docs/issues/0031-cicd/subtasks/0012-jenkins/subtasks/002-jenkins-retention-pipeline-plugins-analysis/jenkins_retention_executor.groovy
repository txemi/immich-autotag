#!/usr/bin/env groovy

/**
 * Jenkins Build Retention and Cleanup Executor
 * 
 * This script implements sustainable retention policies for Jenkins builds and workspaces
 * using Groovy, compatible with multiple execution methods:
 * - Jenkins Script Console (UI)
 * - Jenkins CLI (command line)
 * - Pipeline job (groovy step)
 * - Scheduled maintenance job
 * 
 * See README.md for execution methods and scheduling options.
 */

import jenkins.model.*
import hudson.model.*

// Configuration
def config = [
    buildsToKeep: 4,           // Number of builds to keep per job
    artifactsToKeep: 2,        // Number of builds with artifacts to keep
    dryRun: true,              // Set to false to actually delete
    deleteOrphanedWorkspaces: true,
    workspaceRoot: "/home/ub20jenkins4ub20/txemi/ub20jenkins4ub20/workspace"  // Adjust if needed
]

println """
╔════════════════════════════════════════════════════════════════════════════╗
║        Jenkins Build and Workspace Retention Policy Executor              ║
╚════════════════════════════════════════════════════════════════════════════╝

Configuration:
  Builds to keep per job:    ${config.buildsToKeep}
  Artifacts to keep:         ${config.artifactsToKeep}
  Delete orphaned workspaces: ${config.deleteOrphanedWorkspaces}
  Dry run mode:              ${config.dryRun ? 'ENABLED (preview only)' : 'DISABLED (will delete)'}
  Workspace root:            ${config.workspaceRoot}

═══════════════════════════════════════════════════════════════════════════════
"""

// Track statistics
def stats = [
    jobsProcessed: 0,
    buildsDeleted: 0,
    workspacesDeleted: 0,
    totalSpaceFreed: 0
]

println "[INFO] Starting retention policy execution..."

// ============================================================================
// Section 1: Apply Build Retention Policy
// ============================================================================
println "\n▶ SECTION 1: Applying build retention policy to all jobs"
println "─".multiply(80)

Jenkins.instance.getAllItems(Job.class).each { job ->
    stats.jobsProcessed++
    
    def builds = job.getBuilds().toList()
    if (builds.size() > config.buildsToKeep) {
        builds.sort { it.number }
        def toDelete = builds.take(builds.size() - config.buildsToKeep)
        
        toDelete.each { build ->
            if (config.dryRun) {
                println "[DRY RUN] Job '${job.fullName}' - Would delete build #${build.number} (${build.getDisplayName()})"
            } else {
                try {
                    println "[DELETE] Job '${job.fullName}' - Deleting build #${build.number}"
                    build.delete()
                    stats.buildsDeleted++
                } catch (Exception e) {
                    println "[ERROR] Failed to delete build: ${e.message}"
                }
            }
        }
    }
}

println """
Build retention policy applied:
  Jobs processed: ${stats.jobsProcessed}
  Builds deleted: ${stats.buildsDeleted}
"""

// ============================================================================
// Section 2: Delete Orphaned Workspaces
// ============================================================================
if (config.deleteOrphanedWorkspaces) {
    println "\n▶ SECTION 2: Deleting orphaned workspaces"
    println "─".multiply(80)
    
    def activeWorkspaces = []
    Jenkins.instance.getAllItems(Job.class).each { job ->
        if (job.metaClass.respondsTo(job, 'getWorkspace')) {
            def ws = job.getWorkspace()
            if (ws != null) {
                activeWorkspaces << ws.getRemote()
            }
        }
    }
    
    def dir = new File(config.workspaceRoot)
    if (dir.exists()) {
        def allDirs = dir.listFiles().findAll { it.isDirectory() }
        
        allDirs.each { d ->
            if (!activeWorkspaces.contains(d.absolutePath)) {
                if (config.dryRun) {
                    println "[DRY RUN] Would delete orphan workspace: ${d.name}"
                } else {
                    try {
                        println "[DELETE] Deleting orphan workspace: ${d.name}"
                        d.deleteDir()
                        stats.workspacesDeleted++
                    } catch (Exception e) {
                        println "[ERROR] Failed to delete workspace: ${e.message}"
                    }
                }
            }
        }
        
        println "Orphaned workspaces ${config.dryRun ? 'preview' : 'cleanup'} complete."
    } else {
        println "[WARNING] Workspace root not found: ${config.workspaceRoot}"
    }
}

// ============================================================================
// Summary
// ============================================================================
println """
╔════════════════════════════════════════════════════════════════════════════╗
║                           EXECUTION SUMMARY                               ║
╚════════════════════════════════════════════════════════════════════════════╝

Status:           ${config.dryRun ? '✓ DRY RUN (preview only)' : '✓ EXECUTED (changes made)'}
Jobs processed:   ${stats.jobsProcessed}
Builds deleted:   ${stats.buildsDeleted}
Workspaces deleted: ${stats.workspacesDeleted}

Next steps:
  1. Review the output above
  2. If dry run: check for issues, then set dryRun = false to execute
  3. If executed: monitor disk usage and confirm cleanup worked
  4. Schedule this script to run periodically (see README.md)

═══════════════════════════════════════════════════════════════════════════════
"""

println "[INFO] Retention policy execution complete."
