pipeline {
agent  any  
    stages {
        stage('Build') { 
            steps {
                sh 'hello-world.py'
                
            }
        }
       
                 stage('Test'){
        steps{
             sh 'hello-world.py'
            
            }
        }
        stage('Deploy') { 
            steps {
                sh 'hello-world.py'
            }
        }
    }
}
