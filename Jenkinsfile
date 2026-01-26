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
        stage('Install System Dependencies') {
            steps {
                sh '''
                    apt-get update
                    apt-get install -y git curl nodejs npm shfmt
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
        
        stage('Quality Gate') {
            steps {
                script {
                    echo "Running Quality Gate (relaxed mode)..."
                    sh '''
                        chmod +x scripts/devtools/quality_gate.sh
                        bash scripts/devtools/quality_gate.sh --relaxed --check
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
