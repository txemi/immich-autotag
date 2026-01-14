pipeline {
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
                    apt-get install -y git
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
                        python -c "from immich_autotag import __version__; print(f'✓ immich_autotag version: {__version__}')"
                        python -c "from immich_client import __version__; print(f'✓ immich_client version: {__version__}')"
                        echo "✓ All imports successful"
                    '''
                }
            }
        }
    }
    
    post {
        always {
            echo "Pipeline execution completed at ${new Date()}"
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
