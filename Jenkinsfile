pipeline {
    options {
        // Keep only the last 4 builds
        buildDiscarder(logRotator(numToKeepStr: '4'))
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
                sh '''
                    apt-get update
                    apt-get install -y git curl nodejs npm shfmt
                    rm -rf /var/lib/apt/lists/*
                    
                    # Install jscpd globally for code duplication detection
                    npm install -g jscpd
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
        
        stage('Quality Gate (Shell Script)') {
            steps {
                script {
                    echo "Running Quality Gate (relaxed mode)..."
                    sh '''
                        chmod +x scripts/devtools/quality_gate.sh
                        bash scripts/devtools/quality_gate.sh --level=STANDARD --mode=CHECK
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
                        bash scripts/devtools/quality_gate_py/venv_launcher.sh --level=STANDARD --mode=CHECK
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
            // Archive run outputs (logs, reports, links) generated per execution, excluding albums cache
            archiveArtifacts artifacts: 'logs_local/**/*', excludes: 'logs_local/*/api_cache/*/**', fingerprint: true, allowEmptyArchive: true
            echo "Pipeline execution completed at ${new Date()}"
        }
        success {
            echo "✅ Pipeline succeeded - All stages passed"
        }
        failure {
            echo "❌ Pipeline FAILED - Check logs above"
            // You can add notification here if you want
        }
    }
}
