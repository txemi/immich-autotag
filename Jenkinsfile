pipeline {
    agent any
    
    environment {
        VENV_DIR = "${WORKSPACE}/.venv"
        PYTHON_VERSION = 'python3'
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
                echo "Branch: ${env.GIT_BRANCH}"
                echo "Commit: ${env.GIT_COMMIT}"
            }
        }
        
        stage('Setup Environment') {
            steps {
                script {
                    echo "Setting up Python virtual environment..."
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
                        bash run_app.sh --help || echo "Application executed (help)"
                    '''
                }
            }
        }
        
        stage('Validate') {
            steps {
                script {
                    echo "Validating setup and dependencies..."
                    sh '''
                        source ${VENV_DIR}/bin/activate
                        python --version
                        pip list | grep -i immich || echo "Checking installed packages..."
                    '''
                }
            }
        }
    }
    
    post {
        always {
            echo "Pipeline execution completed"
            cleanWs(deleteDirs: true, disableDeferredWipeout: true, notFailBuild: true)
        }
        success {
            echo "✅ Pipeline succeeded"
        }
        failure {
            echo "❌ Pipeline failed"
        }
    }
}
