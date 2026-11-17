// Declarative Jenkinsfile for Smart Canteen Ordering System CI/CD Pipeline
pipeline {
    agent any

    parameters {
        string(name: 'IMAGE_NAME', defaultValue: 'smart-canteen', description: 'Docker image repository name')
        string(name: 'DOCKER_HUB_USER', defaultValue: 'smartcanteen', description: 'Docker Hub namespace/username')
        choice(name: 'DEPLOY_ENV', choices: ['staging', 'production'], description: 'Deployment target environment')
    }

    environment {
        APP_VERSION = '1.0'
        IMAGE_TAG = "${params.APP_VERSION}.${env.BUILD_NUMBER}"
        FULL_IMAGE = "${params.DOCKER_HUB_USER}/${params.IMAGE_NAME}:${IMAGE_TAG}"
        LATEST_IMAGE = "${params.DOCKER_HUB_USER}/${params.IMAGE_NAME}:latest"
        PYTHON_VENV = "${env.WORKSPACE}/.ci-venv"
    }

    stages {
        stage('Checkout') {
            steps {
                echo "==> Stage 1: Checking out code from SCM repository..."
                checkout scm
                script {
                    echo "Branch: ${env.GIT_BRANCH ?: 'main'}, Commit: ${env.GIT_COMMIT ?: 'HEAD'}"
                }
            }
        }

        stage('Install Dependencies') {
            steps {
                echo "==> Stage 2: Provisioning virtual environment and installing dependencies..."
                sh '''
                    python3 -m venv ${PYTHON_VENV}
                    . ${PYTHON_VENV}/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                '''
            }
        }

        stage('Lint & Code Style') {
            steps {
                echo "==> Stage 3: Running Flake8 static analysis and style checks..."
                sh '''
                    . ${PYTHON_VENV}/bin/activate
                    flake8 app tests --max-line-length=120
                '''
            }
        }

        stage('Test & Coverage Gate') {
            steps {
                echo "==> Stage 4: Executing Pytest test suite with coverage enforcement (>= 80%)..."
                sh '''
                    . ${PYTHON_VENV}/bin/activate
                    mkdir -p reports
                    pytest tests/ -v \
                        --junitxml=reports/junit.xml \
                        --cov=app \
                        --cov-report=xml:reports/coverage.xml \
                        --cov-report=html:reports/coverage_html \
                        --cov-fail-under=80
                '''
            }
        }

        stage('Docker Build') {
            steps {
                echo "==> Stage 5: Building multi-stage container image [${FULL_IMAGE}]..."
                sh '''
                    docker build \
                        --tag ${FULL_IMAGE} \
                        --tag ${LATEST_IMAGE} \
                        --file Dockerfile .
                '''
            }
        }

        stage('Push to Registry') {
            steps {
                echo "==> Stage 6: Pushing tagged container image to Docker Hub..."
                // Requires 'docker-hub-credentials' configured in Jenkins Credentials Provider
                withCredentials([usernamePassword(credentialsId: 'docker-hub-credentials',
                                                 usernameVariable: 'DOCKER_USER',
                                                 passwordVariable: 'DOCKER_PASS')]) {
                    sh '''
                        echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin
                        docker push ${FULL_IMAGE}
                        docker push ${LATEST_IMAGE}
                        docker logout
                    '''
                }
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                echo "==> Stage 7: Deploying manifests to Kubernetes cluster..."
                // Requires 'k8s-kubeconfig' configured in Jenkins Credentials Provider
                withCredentials([file(credentialsId: 'k8s-kubeconfig', variable: 'KUBECONFIG')]) {
                    sh '''
                        # Ensure namespace exists
                        kubectl apply -f k8s/namespace.yaml

                        # Apply configuration and secrets
                        kubectl apply -f k8s/configmap.yaml
                        kubectl apply -f k8s/secret.yaml

                        # Update deployment image to newly built version
                        kubectl set image -f k8s/deployment.yaml smart-canteen=${FULL_IMAGE} --local -o yaml | kubectl apply -f -

                        # Apply service and ingress
                        kubectl apply -f k8s/service.yaml
                        kubectl apply -f k8s/ingress.yaml

                        # Verify zero-downtime rolling update deployment
                        kubectl rollout status deployment/smart-canteen-deployment -n smart-canteen --timeout=120s

                        # Print deployed pod status
                        kubectl get pods,svc -n smart-canteen -o wide
                    '''
                }
            }
        }
    }

    post {
        always {
            echo "==> Pipeline Finished: Archiving test artifacts and test telemetry..."
            junit testResults: 'reports/junit.xml', allowEmptyResults: true
            archiveArtifacts artifacts: 'reports/**', allowEmptyArchive: true

            // Clean up temporary CI virtual environment
            sh 'rm -rf ${PYTHON_VENV}'
        }
        success {
            echo "SUCCESS: Smart Canteen Ordering System CI/CD Pipeline completed successfully! Image: ${FULL_IMAGE}"
        }
        failure {
            echo "FAILURE: CI/CD Pipeline encountered an error. Please inspect stage logs."
        }
    }
}
