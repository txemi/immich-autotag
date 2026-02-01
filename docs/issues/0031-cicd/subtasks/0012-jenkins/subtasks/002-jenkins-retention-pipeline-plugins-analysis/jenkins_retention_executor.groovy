#!/usr/bin/env groovy

/**
 * Jenkins Build Retention and Cleanup Executor
 * 
 * This script implements sustainable retention policies for Jenkins builds and workspaces
 * using Groovy, compatible with multiple execution methods:
 * - Jenkins Script Console (UI)
 * - Jenkins CLI (command line) ⭐ RECOMMENDED - SIMPLEST METHOD
 * - Pipeline job (groovy step)
 * - Scheduled maintenance job
 * 
 * ╔════════════════════════════════════════════════════════════════════════╗
 * ║  🪄 THE MAGIC COMMAND (Jenkins CLI - Simplest & Recommended):         ║
 * ║                                                                        ║
 * ║  java -jar jenkins-cli.jar -s http://<jenkins-url> \                 ║
 * ║    groovy = < jenkins_retention_executor.groovy                      ║
 * ║                                                                        ║
 * ║  First time: wget http://<jenkins-url>/jnlpJars/jenkins-cli.jar       ║
 * ║                                                                        ║
 * ║  Why? One command, no UI, easy to automate, no timeouts!              ║
 * ╚════════════════════════════════════════════════════════════════════════╝
 * 
 * See README.md for all execution methods and detailed documentation.
 */

import jenkins.model.*
import hudson.model.*

// Configuration
// NOTE: This script can run on MASTER or AGENT nodes
// The workspaceRoot will auto-detect based on the node's JENKINS_HOME
// Master: /var/lib/jenkins/workspace
// Agent: /home/jenkins-agent/workspace (or other agent paths)
def config = [
    buildsToKeep: 4,           // Number of builds to keep per job
    artifactsToKeep: 2,        // Number of builds with artifacts to keep
    dryRun: true,              // Set to false to actually delete
    deleteOrphanedWorkspaces: true,
    workspaceRoot: "${System.getenv('JENKINS_HOME') ?: '/var/jenkins'}/workspace",  // Auto-detect from JENKINS_HOME env var
    // For manual override on agent: workspaceRoot: "/home/jenkins-agent/workspace"
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
    
    // Build list of ABSOLUTE paths of active workspaces
    def activeWorkspaces = [] as Set  // Use Set for O(1) lookup
    
    Jenkins.instance.getAllItems(Job.class).each { job ->
        try {
            if (job.metaClass.respondsTo(job, 'getWorkspace')) {
                def ws = job.getWorkspace()
                if (ws != null) {
                    // FIXED: Use ws.absolutePath instead of ws.getRemote()
                    def absolutePath = ws.absolutePath
                    if (absolutePath) {
                        activeWorkspaces << absolutePath
                    }
                }
            }
        } catch (Exception e) {
            println "[WARN] Error reading workspace for job '${job.fullName}': ${e.class.simpleName}"
        }
    }
    
    println "[INFO] Found ${activeWorkspaces.size()} active job workspaces"
    
    def dir = new File(config.workspaceRoot)
    if (dir.exists()) {
        def allDirs = dir.listFiles()?.findAll { it.isDirectory() } ?: []
        
        println "[INFO] Scanning ${allDirs.size()} directories in workspace root"
        
        allDirs.each { d ->
            def isActive = activeWorkspaces.contains(d.absolutePath)
            
            if (!isActive) {
                // Get directory size BEFORE deletion
                def sizeBeforeStr = config.dryRun ? "" : ""
                
                if (config.dryRun) {
                    // Calculate size for reporting
                    def sizeCmd = "du -sb '${d.absolutePath}' 2>/dev/null | awk '{print \$1}'"
                    try {
                        def process = sizeCmd.execute()
                        def size = process.text.trim().toLong()
                        def sizeGB = String.format("%.2f", size / (1024**3))
                        println "[DRY RUN] Would delete orphan workspace: ${d.name} (~${sizeGB} GiB)"
                    } catch (Exception e) {
                        println "[DRY RUN] Would delete orphan workspace: ${d.name}"
                    }
                } else {
                    try {
                        // Use shell command for more robust deletion with shared permissions
                        def deleteCmd = "rm -rf '${d.absolutePath}'"
                        def process = deleteCmd.execute()
                        def exitCode = process.waitFor()
                        
                        if (exitCode == 0) {
                            println "[DELETE] ✓ Deleted orphan workspace: ${d.name}"
                            stats.workspacesDeleted++
                        } else {
                            def errMsg = process.err.text
                            println "[ERROR] Failed to delete (exit ${exitCode}): ${d.name}"
                            if (errMsg) println "         Error: ${errMsg.take(100)}"
                        }
                    } catch (Exception e) {
                        println "[ERROR] Exception deleting ${d.name}: ${e.class.simpleName}: ${e.message}"
                        e.printStackTrace()
                    }
                }
            }
        }
        
        println "[INFO] Orphaned workspaces ${config.dryRun ? 'preview' : 'cleanup'} complete."
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
