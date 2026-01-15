pipeline {
    options {
        // Short debounce to collapse rapid pushes (seconds)
        quietPeriod(10)
        // We'll perform checkout explicitly so we can abort outdated builds early
        skipDefaultCheckout(true)
    }
    agent {
        docker {
            image 'python:3.11-slim'
            args '-v $HOME/.cache:/root/.cache -v $HOME/.config/immich_autotag:/root/.config/immich_autotag:ro --user root'
        }
    }
    
    environment {
        PYTHONUNBUFFERED = '1'
    }
    
    stages {
        stage('Start: Clean workspace') {
            steps {
                script {
                    // Require Workspace Cleanup Plugin to be present — if missing, the pipeline will fail here so operators can install it
                    cleanWs()
                    echo 'Workspace cleaned at start of build.'
                }
            }
        }
        stage('Checkout & Abort if outdated') {
            steps {
                // ensure git is present in container before calling checkout scm
                script {
                    sh '''
                        set -x
                        export DEBIAN_FRONTEND=noninteractive
                        apt-get update -yqq || true
                        apt-get install -yqq git ca-certificates --no-install-recommends || true
                        rm -rf /var/lib/apt/lists/* || true
                    '''
                    // perform explicit checkout and abort quickly if this job is not building the branch HEAD
                    checkout scm
                    // Git (inside container) may refuse to operate if the mounted workspace ownership
                    // differs from the container user. Allow this workspace as safe to avoid
                    // "detected dubious ownership" errors.
                    sh '''
                        set -x
                        if [ -n "$WORKSPACE" ]; then
                            git config --global --add safe.directory "$WORKSPACE" || true
                        fi
                    '''
                    def branch = env.BRANCH_NAME ?: env.GIT_BRANCH ?: ''
                    if (!branch) {
                        echo "BRANCH_NAME / GIT_BRANCH not set; skipping outdated-check"
                    } else {
                        sh "git fetch origin ${branch} --quiet || true"
                        def localHead = sh(returnStdout: true, script: 'git rev-parse HEAD').trim()
                        def remoteHead = sh(returnStdout: true, script: "git rev-parse origin/${branch} || true").trim()
                        if (remoteHead && localHead != remoteHead) {
                            echo "This build targets commit ${localHead} but origin/${branch} is ${remoteHead}. Aborting outdated build."
                            catchError(buildResult: 'ABORTED', stageResult: 'ABORTED') {
                                error('Outdated build — aborting early')
                            }
                        } else {
                            echo "Build is up-to-date (HEAD matches origin/${branch}). Continuing."
                        }
                    }
                }
            }
        }
        stage('Install System Dependencies') {
            steps {
                sh '''
                    apt-get update
                    apt-get install -y git curl
                    rm -rf /var/lib/apt/lists/*
                '''
            }
        }
        
        stage('Setup Environment') {
            steps {
                script {
                    echo "Setting up Python environment..."
                    sh '''
                        chmod +x setup_venv.sh
                        bash setup_venv.sh
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
            // Archive profiling artifacts first (if present), then key logs, then the rest
            script {
                try {
                    archiveArtifacts artifacts: 'logs_local/profiling/**', fingerprint: true, allowEmptyArchive: true
                } catch (err) {
                    echo "No profiling artifacts to archive or archive failed: ${err}"
                }
                // Archive essential run statistics and main logs
                archiveArtifacts artifacts: 'logs_local/**/run_statistics.yaml, logs_local/**/immich_autotag_full_output.log', allowEmptyArchive: true, fingerprint: true
                // Archive everything else as a fallback
                archiveArtifacts artifacts: 'logs_local/**/*', allowEmptyArchive: true

                echo "Pipeline execution completed at ${new Date()}"
                // Final cleanup to free disk space (requires Workspace Cleanup Plugin)
                cleanWs()
                echo 'Workspace cleaned at end of build.'
            }
        }
        success {
            echo "✅ Pipeline succeeded - All stages passed"
        }
        failure {
            echo "❌ Pipeline FAILED - Check logs above"
            // Puedes añadir notificación aquí si quieres
        }
    }
}
