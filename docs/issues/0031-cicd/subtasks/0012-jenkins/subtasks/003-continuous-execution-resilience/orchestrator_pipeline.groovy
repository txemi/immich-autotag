pipeline {
  agent any

  options {
    disableConcurrentBuilds()
    buildDiscarder(logRotator(numToKeepStr: '30'))
    timeout(time: 24, unit: 'HOURS')
    timestamps()
  }

  parameters {
    booleanParam(name: 'LOOP_ENABLED', defaultValue: true, description: 'Kill switch. Disable to stop the loop safely.')
    string(name: 'TARGET_JOB', defaultValue: 'immich-autotag/ops%2Fcontinuous-processing', description: 'Target multibranch job full name. Copy from Jenkins job page (Full project name).')
    string(name: 'SLEEP_SECONDS_SUCCESS', defaultValue: '20', description: 'Pause after SUCCESS/UNSTABLE.')
    string(name: 'SLEEP_SECONDS_FAILURE', defaultValue: '60', description: 'Pause after FAILURE.')
    string(name: 'SLEEP_SECONDS_ABORTED', defaultValue: '30', description: 'Pause after ABORTED (if loop continues).')
    string(name: 'MAX_CYCLES', defaultValue: '0', description: '0 = infinite loop. Any positive value = max cycles.')
    string(name: 'MAX_CONSECUTIVE_FAILURES', defaultValue: '12', description: 'Stop loop after this many consecutive failures.')
    booleanParam(name: 'STOP_ON_ABORTED', defaultValue: true, description: 'Stop loop immediately if child build is ABORTED.')
  }

  environment {
    SAFE_SUCCESS = 'SUCCESS'
    SAFE_UNSTABLE = 'UNSTABLE'
    SAFE_FAILURE = 'FAILURE'
    SAFE_ABORTED = 'ABORTED'
    SAFE_NOT_BUILT = 'NOT_BUILT'
  }

  stages {
    stage('Continuous Orchestration Loop') {
      steps {
        script {
          if (!params.LOOP_ENABLED) {
            echo '[ORCH] LOOP_ENABLED=false. Exiting by configuration.'
            return
          }

          int cycles = 0
          int consecutiveFailures = 0

          int maxCycles = (params.MAX_CYCLES as Integer)
          int maxConsecutiveFailures = (params.MAX_CONSECUTIVE_FAILURES as Integer)
          int sleepSuccess = (params.SLEEP_SECONDS_SUCCESS as Integer)
          int sleepFailure = (params.SLEEP_SECONDS_FAILURE as Integer)
          int sleepAborted = (params.SLEEP_SECONDS_ABORTED as Integer)

          echo "[ORCH] Starting loop: TARGET_JOB='${params.TARGET_JOB}', MAX_CYCLES=${maxCycles}, MAX_CONSECUTIVE_FAILURES=${maxConsecutiveFailures}"

          while (params.LOOP_ENABLED && (maxCycles == 0 || cycles < maxCycles)) {
            cycles += 1
            echo "[ORCH] Cycle ${cycles}: launching '${params.TARGET_JOB}'"

            def child = build job: params.TARGET_JOB, wait: true, propagate: false
            String childResult = (child?.result ?: env.SAFE_NOT_BUILT).toString()
            String childUrl = (child?.absoluteUrl ?: 'n/a').toString()

            echo "[ORCH] Cycle ${cycles}: result=${childResult}, childUrl=${childUrl}"

            if (childResult == env.SAFE_SUCCESS || childResult == env.SAFE_UNSTABLE) {
              consecutiveFailures = 0
              echo "[ORCH] Sleeping ${sleepSuccess}s after ${childResult}."
              sleep time: sleepSuccess, unit: 'SECONDS'
              continue
            }

            if (childResult == env.SAFE_ABORTED) {
              if (params.STOP_ON_ABORTED) {
                echo '[ORCH] Child build ABORTED and STOP_ON_ABORTED=true. Stopping loop.'
                currentBuild.result = env.SAFE_ABORTED
                break
              }
              echo "[ORCH] Child build ABORTED but loop continues. Sleeping ${sleepAborted}s."
              sleep time: sleepAborted, unit: 'SECONDS'
              continue
            }

            // FAILURE / NOT_BUILT / any other non-success outcome
            consecutiveFailures += 1
            echo "[ORCH] Consecutive failures: ${consecutiveFailures}/${maxConsecutiveFailures}. Sleeping ${sleepFailure}s."

            if (consecutiveFailures >= maxConsecutiveFailures) {
              echo '[ORCH] Max consecutive failures reached. Stopping loop for safety.'
              currentBuild.result = env.SAFE_FAILURE
              break
            }

            sleep time: sleepFailure, unit: 'SECONDS'
          }

          echo "[ORCH] Loop finished after ${cycles} cycle(s)."
        }
      }
    }
  }

  post {
    always {
      echo '[ORCH] Orchestrator finished.'
    }
  }
}
