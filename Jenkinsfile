pipeline {
    agent { label 'deploy'}
    stages {
        stage('Build') { 
            steps {
                sh 'python hello-world.py'
            }
        }
        stage('Test') { 
            steps {
                 sh 'python hello-world.py'
            }
        }
        stage('Deploy') { 
            steps {
                sh 'python hello-world.py'
            }
        }
    }
}
