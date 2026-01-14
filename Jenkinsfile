pipeline {
    agent {
        docker {
            image 'python:3.11-slim'
            args '-v $HOME/.cache:/root/.cache --user root'
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
        
        stage('Run Application') {
            steps {
                script {
                    echo "Running immich-autotag application..."
                    sh '''
                        chmod +x run_app.sh
                        bash run_app.sh --help
                    '''
                }
            }
        }
        
        stage('Validate') {
            steps {
                sh '''
                    python --version
                    pip list | grep -i immich || echo "Checking packages..."
                '''
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
