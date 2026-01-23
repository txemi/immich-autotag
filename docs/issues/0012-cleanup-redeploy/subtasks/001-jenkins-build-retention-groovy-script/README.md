# Jenkins Build Retention Utility Script

## Contexto

En Jenkins multibranch, la política de retención de builds no siempre se aplica correctamente a los jobs hijos, lo que puede provocar acumulación de builds antiguos y consumo excesivo de disco. Para solucionarlo, se puede usar un script Groovy en la Script Console de Jenkins que borra todos los builds antiguos, dejando solo los N más recientes en cada job.

## Script Groovy para limpieza de builds antiguos

> **Uso:** Copia y pega este script en la Script Console de Jenkins (`http://<jenkins>/script`).
> 
> **Precaución:** ¡Revisa el número de builds a conservar antes de ejecutar!

```groovy
Jenkins.instance.getAllItems(Job.class).each { job ->
  def builds = job.getBuilds().toList() // Convierte a lista modificable
  if (builds.size() > 4) {
    builds.sort { it.number } // Ordena por número de build (ascendente)
    builds.take(builds.size() - 4).each { it.delete() } // Borra todos menos los 4 más recientes
  }
}
```

- Cambia el número `4` por el número de builds que quieras conservar.
- El script recorre todos los jobs y elimina los builds antiguos.
- No borra jobs completos ni builds marcados como "Keep forever" (candado).

---

# Scheduled Execution (Automation)

You can automate the periodic execution of this Groovy script in Jenkins to ensure old builds are regularly cleaned up, even if the built-in retention policy fails. Here are some options:

## 1. Scheduled Job with the Scriptler Plugin
- Install the [Scriptler Plugin](https://plugins.jenkins.io/scriptler/) in Jenkins.
- Save this Groovy script as a Scriptler script.
- Create a new Jenkins job (Freestyle or Pipeline) that runs the Scriptler script on a schedule (e.g., daily or weekly using cron syntax).

## 2. Groovy Postbuild Plugin
- Use the [Groovy Postbuild Plugin](https://plugins.jenkins.io/groovy-postbuild/) to run the script as a post-build action in a dedicated maintenance job.
- Schedule the job to run periodically.

## 3. Admin Pipeline Job
- Create a dedicated Pipeline job for Jenkins administration.
- Use a `groovy` step to run the script:

```groovy
node {
    // ...
    groovy '''
    // Paste the build cleanup script here
    '''
}
```
- Schedule the pipeline with a cron trigger.

## 4. Manual Reminder
- Add a calendar reminder for sysadmins to run the script manually from the Script Console every X weeks/months.

---

# English Version

## Jenkins Build Retention Utility Script

### Context

In Jenkins multibranch setups, the build retention policy does not always apply correctly to child jobs, which can lead to accumulation of old builds and excessive disk usage. To solve this, you can use a Groovy script in the Jenkins Script Console to delete all old builds, keeping only the N most recent ones per job.

### Groovy Script for Cleaning Old Builds

> **Usage:** Copy and paste this script into the Jenkins Script Console (`http://<jenkins>/script`).
> 
> **Caution:** Review the number of builds to keep before running!

```groovy
Jenkins.instance.getAllItems(Job.class).each { job ->
  def builds = job.getBuilds().toList() // Make a mutable list
  if (builds.size() > 4) {
    builds.sort { it.number } // Sort by build number (ascending)
    builds.take(builds.size() - 4).each { it.delete() } // Delete all but the 4 most recent
  }
}
```

- Change the number `4` to the number of builds you want to keep.
- The script iterates over all jobs and deletes old builds.
- It does not delete entire jobs or builds marked as "Keep forever" (lock icon).

### Automation

You can schedule this script to run automatically using Scriptler, a dedicated admin pipeline, or a periodic reminder.

---

**Relacionado con:**
- [Issue 0012: Cleanup and Redeployment](../../plan.md)
- [Manual Cleanup Links](../../manual_cleanup_links.md)
- [Issue 0014: Jenkins Pipeline Containerization](../../../0014-jenkins-pipeline-containerization/index.md)
