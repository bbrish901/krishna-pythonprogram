pipeline {
agent  any  
    stages {
        stage('Build') { 
            steps {
                python 'hello-world.py'
                
            }
        }
       
                 stage('Test'){
        steps{
             python 'hello-world.py'
            
            }
        }
        stage('Deploy') { 
            steps {
                python 'hello-world.py'
            }
        }
    }
}
