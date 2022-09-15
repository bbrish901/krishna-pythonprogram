pipeline {
    agent { label 'jenkins slave'}
           
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
        stage('Setup') {
             steps {
                  dir ('thursday') {
                  sh 'rm -rf'
                  }
               }
}
        stage('Deploy') { 
            steps {
                sh 'python hello-world.py'
            }
        }
    }
}
