pipeline {
    agent { label 'deploy server'}
           
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
