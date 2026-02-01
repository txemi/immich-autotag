#!/usr/bin/env groovy

/**
 * Jenkins Agent Workspace Cleanup Script
 * 
 * Purpose: Clean orphaned workspace directories on Jenkins agent nodes
 * 
 * Usage: Paste this script in Jenkins Script Console and click "Run"
 * 
 * This script is optimized for agent nodes with workspaces in /home/
 * and will delete ALL directories except active Jenkins workspaces
 */

import java.io.File

// Configuration - AUTO-DETECT agent workspace location
def agentWorkspaceRoot = new File(System.getenv('JENKINS_HOME') ?: '/var/lib/jenkins')
def workspacePath = new File(agentWorkspaceRoot, 'workspace')

// For agents, override to the actual agent workspace path
if (System.getenv('JENKINS_HOME')?.contains('/home/')) {
    workspacePath = new File(System.getenv('JENKINS_HOME'), 'workspace')
}

println """
╔════════════════════════════════════════════════════════════════════════════╗
║            Agent Workspace Orphan Cleanup - EXECUTION MODE               ║
╚════════════════════════════════════════════════════════════════════════════╝

Node: ${System.getenv('HOSTNAME') ?: 'unknown'}
Workspace root: ${workspacePath.absolutePath}
JENKINS_HOME: ${System.getenv('JENKINS_HOME') ?: 'not set'}

═══════════════════════════════════════════════════════════════════════════════
"""

// Validate workspace exists
if (!workspacePath.exists()) {
    println "[ERROR] Workspace path does not exist: ${workspacePath.absolutePath}"
    return
}

// Get total size BEFORE
def totalSizeBefore = 0
workspacePath.eachDir { dir ->
    totalSizeBefore += calculateDirSize(dir)
}
def totalGiBBefore = String.format("%.2f", totalSizeBefore / (1024**3))

println "[INFO] Total workspace size: ${totalGiBBefore} GiB"
println "[INFO] Scanning directories..."

// Track active workspaces from Jenkins
def activeWorkspaces = [] as Set
Jenkins.instance.getAllItems(hudson.model.Job.class).each { job ->
    try {
        if (job.metaClass.respondsTo(job, 'getWorkspace')) {
            def ws = job.getWorkspace()
            if (ws != null) {
                activeWorkspaces << ws.absolutePath
            }
        }
    } catch (Exception e) {
        // Ignore jobs without workspaces
    }
}

println "[INFO] Found ${activeWorkspaces.size()} active job workspaces"
println ""
println "▶ DELETING ORPHANED DIRECTORIES"
println "─".multiply(80)

def deletedCount = 0
def failedCount = 0
def totalSpaceFreed = 0

workspacePath.eachDir { dir ->
    if (!activeWorkspaces.contains(dir.absolutePath)) {
        def dirSize = calculateDirSize(dir)
        def dirSizeGB = String.format("%.2f", dirSize / (1024**3))
        
        try {
            if (deleteDirectory(dir)) {
                println "[DELETE] ✓ ${dir.name} (~${dirSizeGB} GiB)"
                deletedCount++
                totalSpaceFreed += dirSize
            } else {
                println "[ERROR]  ✗ ${dir.name} (~${dirSizeGB} GiB) - could not delete"
                failedCount++
            }
        } catch (Exception e) {
            println "[ERROR]  ✗ ${dir.name} - ${e.message}"
            failedCount++
        }
    }
}

println ""
println "▶ CLEANUP SUMMARY"
println "─".multiply(80)

def totalSizeAfter = 0
workspacePath.eachDir { dir ->
    totalSizeAfter += calculateDirSize(dir)
}
def totalGiBAfter = String.format("%.2f", totalSizeAfter / (1024**3))
def totalGiBFreed = String.format("%.2f", totalSpaceFreed / (1024**3))

println "Directories deleted: ${deletedCount}"
println "Failed deletions:    ${failedCount}"
println "Space freed:         ${totalGiBFreed} GiB"
println "Remaining:           ${totalGiBAfter} GiB"
println ""

if (failedCount == 0 && deletedCount > 0) {
    println "✅ Cleanup completed successfully!"
} else if (failedCount > 0) {
    println "⚠️  Cleanup completed with ${failedCount} errors"
} else {
    println "ℹ️  No orphaned directories found to delete"
}

println ""

// Helper functions
def calculateDirSize(File dir) {
    try {
        long size = 0
        dir.eachFileRecurse { file ->
            size += file.size()
        }
        return size
    } catch (Exception e) {
        return 0
    }
}

def deleteDirectory(File dir) {
    try {
        if (dir.isDirectory()) {
            // Try Groovy deleteDir first
            return dir.deleteDir()
        }
    } catch (Exception e) {
        try {
            // Fallback to runtime shell command
            def cmd = "rm -rf '${dir.absolutePath}'"
            def process = cmd.execute()
            return process.waitFor() == 0
        } catch (Exception e2) {
            return false
        }
    }
    return false
}
