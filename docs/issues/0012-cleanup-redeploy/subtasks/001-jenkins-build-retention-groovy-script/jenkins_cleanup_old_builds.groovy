// Jenkins Groovy Script: Cleanup Old Builds in Multibranch Jobs
// Deletes all but the N most recent builds in every Jenkins job.
// Usage: Copy and paste into Jenkins Script Console or Scriptler.
// Change the value of 'buildsToKeep' as needed.

// ---
// Section 1: Delete old builds, keep only the N most recent per job

import jenkins.model.*
import hudson.model.*

def buildsToKeep = 4 // Number of builds to keep per job

Jenkins.instance.getAllItems(Job.class).each { job ->
    def builds = job.getBuilds().toList() // Make a mutable list
    if (builds.size() > buildsToKeep) {
        builds.sort { it.number } // Sort by build number (ascending)
        builds.take(builds.size() - buildsToKeep).each { it.delete() } // Delete all but the N most recent
    }
}

// ---
// Section 2: Delete orphaned workspaces (folders in workspace root not used by any active job)
// This helps reclaim disk space from jobs/branches that no longer exist in Jenkins.

def workspaceRoot = "/home/ub20jenkins4ub20/txemi/ub20jenkins4ub20/workspace" // Adjust if needed

def activeWorkspaces = []
Jenkins.instance.getAllItems(Job.class).each { job ->
    def ws = job.getWorkspace()
    if (ws != null) {
        activeWorkspaces << ws.getRemote()
    }
}

def dir = new File(workspaceRoot)
if (dir.exists()) {
    def allDirs = dir.listFiles().findAll { it.isDirectory() }
    allDirs.each { d ->
        if (!activeWorkspaces.contains(d.absolutePath)) {
            println "Deleting orphan workspace: ${d.absolutePath}"
            d.deleteDir()
        }
    }
    println "Orphan workspace cleanup complete."
} else {
    println "Workspace root not found: ${workspaceRoot}"
}
