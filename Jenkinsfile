// ==================== CONFIG FLAGS ====================
def ENABLE_JENKINS_TAGGING = true // Set to true to enable GitHub tagging
// Auto-chain: on success the build re-triggers itself, so the batch keeps walking the library
// without anyone pressing a button. It belongs ONLY to the operational branch: on any other
// branch it would spin a second infinite loop competing for the SAME single agent
// (the one carrying the `immich-batch` label), where each run can take hours. main is
// for validating, not for processing the library.
def ENABLE_AUTO_CHAIN = (env.BRANCH_NAME == 'ops/batch-processing')
                                  // (keeps the batch-processing chain self-perpetuating
                                  // without external dispatch). Failure stops the chain
                                  // by design — re-enable manually after investigating.

// Helper for tagging (debe estar fuera del pipeline)
def tagBuild(String type) {
    def tagName = "jenkins-${type}-${env.BUILD_NUMBER ?: 'manual'}-${env.GIT_COMMIT ?: 'manual'}"
    echo "🏷️ Creando tag GitHub (${type}): ${tagName}"
    try {
        sh "git config user.name 'jenkins'"
        sh "git config user.email 'jenkins@localhost'"
        sh "git tag ${tagName}"
        withCredentials([usernamePassword(
            credentialsId: 'app_github_para_ubuntu20jenkins.ad3.lab',
            usernameVariable: 'GH_USER',
            passwordVariable: 'GH_TOKEN'
        )]) {
            sh "git remote set-url origin https://\${GH_USER}:\${GH_TOKEN}@github.com/txemi/immich-autotag.git"
            sh "git push origin ${tagName}"
        }
    } catch (e) {
        echo "⚠️ GitHub tagging failed (non-fatal): ${e.message}"
    }
}
pipeline {
    options {
        // Keep last 30 builds or 30 days, whichever is smaller. The previous
        // value of 4 was effectively bypassed because every SUCCESS build was
        // pinned via `currentBuild.keepLog = true` (now removed in the
        // success post-action below), so old builds never rotated and ate
        // tens of GB on the master.
        buildDiscarder(logRotator(numToKeepStr: '30', daysToKeepStr: '30'))
    }
    agent {
        docker {
            image 'python:3.11-slim'
            // Pin to the batch agent: the checkpoint chain (logs_local/) lives in that
            // node's workspace, and sequential single-node execution is required
            // (see issue 004-active-run-monitoring). Without a label the build can land
            // on the Windows agent (no docker) or the controller.
            //
            // The label is a PURPOSE, not a hostname. It used to say
            // 'ub20jenkins4ub20', which happens to work because Jenkins exposes every
            // node's own name as an implicit label -- but that is not a label anyone
            // declared: this controller only defines two, `linux` and `windows`. Binding
            // the pipeline to a machine name means renaming or replacing that machine
            // requires a code change and a PR to a protected branch, and it silently
            // bypasses the label scheme.
            //
            // `immich-batch` is declared on the node in Jenkins (2026-08-10). Moving the
            // batch to another machine is now a checkbox there, not a commit here. NOTE:
            // it is deliberately assigned to ONE node -- until the checkpoint stops
            // living in a node's workspace, a second node would reprocess from zero.
            label 'immich-batch'
            // Mounts ~/.ssh from host into the container as read-only for private key and known_hosts access
            // Ensure $HOME/.ssh exists and contains the required key and known_hosts files
            //
            // ⚠️ NO se monta el `$HOME/.cache` DEL AGENTE en `/root/.cache`. Rompe la CI de
            // OTROS repos, y con 12 horas de retardo.
            //
            // Este contenedor corre con `--user root` (lo necesita: los montajes de abajo van a
            // `/root/...`, que un usuario no-root no podria leer). Y dentro del contenedor
            // HOME=/root, asi que aquel `-v $HOME/.cache:/root/.cache` resultaba ser el
            // `~/.cache` DEL AGENTE, montado en escritura y escrito por uid 0. Resultado:
            // cientos de ficheros de root dentro de la cache de `uv` del agente, que a partir de
            // ahi puede LEERLA pero no ACTUALIZARLA.
            //
            // Se manifiesta lejos y tarde: los otros gates del nodo siguen verdes mientras a `uv`
            // le baste la cache tal cual. Cuando toca refrescar (para un TAG, uv depende del
            // "fast path" de la API de GitHub, y ese cubo anonimo son 60/h por IP publica
            // COMPARTIDA por todo el homelab), hace un `git fetch` de verdad, necesita escribir,
            // y falla con `Git operation failed`. La receta de darnlink lo reporta como
            // "bad ref / no network", que apunta a dos cosas que estan bien.
            // Medido el 2026-08-11: 327 ficheros de root y `txnet1__darnlink_gate #173/#174` en
            // rojo, 11 minutos despues de que este job corriera. Ver `txnet1`, Regla 4 de
            // `systems/jenkins/reglas.md`.
            //
            // La cache pasa a ser del CONTENEDOR: se muere con el y no toca el home de nadie.
            // Se pierde el reuso entre builds; el precio de reconstruirla es mucho menor que
            // dejar la CI de la flota en rojo con un mensaje que apunta a otro sitio.
            //
            // ⚠️ Lo que NO se toca aqui, a proposito: `--user root`. Quitarlo tiene su propio
            // riesgo -- los dos montajes de abajo van a `/root/...`, y un usuario no-root no
            // podria leerlos-- y ademas seguiria dejando el WORKSPACE con ficheros de root, que
            // es otro sintoma del mismo problema y hoy lo barre un cron. Eso es una segunda
            // decision, no esta.
            args '-v $HOME/.config/immich_autotag:/root/.config/immich_autotag:ro -v $HOME/.ssh:/root/.ssh:ro --user root -e XDG_CACHE_HOME=/tmp/cache -e UV_CACHE_DIR=/tmp/cache/uv'
        }
    }
    
    environment {
        PYTHONUNBUFFERED = '1'
    }
    
    stages {
        stage('Clean Python Caches') {
            steps {
                script {
                    echo "Cleaning Python cache directories to prevent permission issues..."
                    sh '''
                        # Remove cache directories that can cause permission issues in Jenkins
                        rm -rf .mypy_cache .pytest_cache __pycache__ *.pyc
                        find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
                        find . -type f -name '*.pyc' -delete 2>/dev/null || true
                        echo "✓ Cache directories cleaned"
                    '''
                }
            }
        }
        
        stage('Install System Dependencies') {
            steps {
                script {
                    echo "[JENKINS] Installing all system and dev tools via setup_venv.sh --dev..."
                    sh '''
                        chmod +x setup_venv.sh
                        # use clean in case immich server updated version and we need to refresh client
                        bash setup_venv.sh --clean --dev 
                    '''
                }
            }
        }
        
        stage('Validate Installation') {
            steps {
                script {
                    echo "Validating installation..."
                    sh '''
                        . .venv/bin/activate
                        python -c "from immich_autotag import __version__; print(f'✓ immich_autotag {__version__}')"
                        python -c "import immich_client; print('✓ immich_client installed')"
                        echo "✓ All imports successful"
                    '''
                }
            }
        }
        stage('Quality Gate (Python OO)') {
            steps {
                script {
                    echo "================ PYTHON QUALITY GATE (MODULAR OO VERSION) ================"
                    echo "[PYTHON QUALITY GATE] Ejecutando Quality Gate Python (modular OO, attrs, enum, subprocess, type-safe)"
                    sh '''
                        # Configure git safe.directory to avoid ownership errors
                        git config --global --add safe.directory "$PWD"
                        chmod +x scripts/devtools/quality_gate_py/venv_launcher.sh
                        # TODO: Temporary workaround - skipping `check_mypy` in CI until
                        # type/model discrepancies are resolved. Remove this flag and
                        # revert to full Quality Gate once fixes are applied.
                        # FIXME: ensure we don't forget to remove this.
                        #bash scripts/devtools/quality_gate_py/venv_launcher.sh --level=STANDARD --mode=CHECK --skip-checks=check_mypy
                        bash scripts/devtools/quality_gate_py/venv_launcher.sh --level=STANDARD --mode=CHECK 
                    '''
                }
            }
        }
        stage('Quality Gate (Docs Links)') {
            steps {
                script {
                    echo "================ DOCS LINK GATE (darnlink) ================"
                    echo "[DOCS LINK GATE] Checking uuid-anchored Markdown links (read-only, no --write)"
                    sh '''
                        git config --global --add safe.directory "$PWD"
                        # darnlink runs via uvx; ensure uv is available in a
                        # predictable location (user site, not a global pip).
                        export PATH="$HOME/.local/bin:$PATH"
                        command -v uvx >/dev/null 2>&1 || python3 -m pip install --quiet --user uv
                        bash scripts/devtools/darnlink_docs_gate.sh .
                    '''
                }
            }
        }
        stage('Quality Gate (Shell Script)') {
            when {
                expression { false } // Disabled: deprecated shell quality gate. Keep stage for history, skip execution.
            }
            steps {
                script {
                    echo '🚨🚨 DEPRECATED: QUALITY GATE (SHELL SCRIPT) - USE PYTHON VERSION INSTEAD 🚨🚨'
                    echo "Running Quality Gate (relaxed mode)..."
                    sh '''
                        chmod +x scripts/devtools/quality_gate.sh
                        bash scripts/devtools/quality_gate.sh --level=STANDARD --mode=CHECK
                    '''
                }
            }
        }



        stage('Run Application') {
            steps {
                script {
                    echo "Running immich-autotag application..."
                    sh '''
                        chmod +x run_app.sh
                        bash run_app.sh
                    '''
                }
            }
        }
    }
    
    post {
        always {
            // Archive run-dir outputs only. Two changes vs the previous pattern:
            //   * `*_PID*` matches the run dir naming scheme and skips `_archive/`,
            //     which the wrap-around fills with snapshots of completed cycles
            //     and grows unbounded over time.
            //   * `fingerprint: false` — SHA1ing all run files dominated build wall
            //     time (5-47h per build for the post-actions phase). We don't
            //     consume these artifacts across pipelines, so the fingerprints
            //     have no consumer.
            archiveArtifacts artifacts: 'logs_local/*_PID*/**', excludes: 'logs_local/*/api_cache/**', fingerprint: false, allowEmptyArchive: true
            echo "Pipeline execution completed at ${new Date()}"
        }

        success {
            echo "✅ Pipeline succeeded - All stages passed"
            script {
                // Do NOT pin successful builds with keepLog=true. Pinning bypasses
                // buildDiscarder and historical builds accumulate forever, filling
                // the master disk (we hit 99% in May 2026). If a specific build
                // needs to be retained, mark it manually from the UI instead.
                if (ENABLE_JENKINS_TAGGING) {
                    tagBuild('success')
                } else {
                    echo "[INFO] Jenkins tagging and push is disabled by ENABLE_JENKINS_TAGGING flag."
                }
                if (ENABLE_AUTO_CHAIN) {
                    echo "🔁 Auto-chain enabled: triggering next build on this branch"
                    build job: env.JOB_NAME, wait: false, propagate: false
                } else {
                    echo "[INFO] Auto-chain disabled by ENABLE_AUTO_CHAIN flag."
                }
            }
        }
        failure {
            echo "❌ Pipeline FAILED - Check logs above"
            script {
                if (ENABLE_JENKINS_TAGGING) {
                    tagBuild('fail')
                } else {
                    echo "[INFO] Jenkins tagging and push is disabled by ENABLE_JENKINS_TAGGING flag."
                }
            }
        }
        aborted {
            echo "⚠️ Pipeline ABORTED - Build was cancelled"
            script {
                if (ENABLE_JENKINS_TAGGING) {
                    tagBuild('abort')
                } else {
                    echo "[INFO] Jenkins tagging and push is disabled by ENABLE_JENKINS_TAGGING flag."
                }
            }
        }
    }
}
