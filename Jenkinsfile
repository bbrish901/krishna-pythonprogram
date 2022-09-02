pipeline {
    agent { label 'deploy'}
           
    stages {
        stage('Build') { 
            steps {
                sh 'python hello-world.py'
                sh '172.31.87.43 '
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
