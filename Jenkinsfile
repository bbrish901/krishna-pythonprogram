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
        stage('Creating Artifact'){
        steps{
            archiveArtifacts artifacts: '**', followSymlinks: false
        }
    }
        stage('Deploy') { 
            steps {
                sh 'python hello-world.py'
            }
        }
    }
}
