// Jenkins Groovy Script: Cleanup Old Builds in Multibranch Jobs
// Deletes all but the N most recent builds in every Jenkins job.
// Usage: Copy and paste into Jenkins Script Console or Scriptler.
// Change the value of 'buildsToKeep' as needed.

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
