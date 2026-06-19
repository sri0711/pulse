pipeline {
  agent any

  triggers {
    cron('H * * * *')
  }

  stages {
    stage('Create Jenkins jobs') {
      steps {
        script {
          def projects = readJSON file: 'projects.json'
          def quote = { s -> s.toString().replace("'", "\\'") }

          projects.each { project ->
            def jobName = project.jobName ?: project.name
            def branch = project.gitBranch ?: 'main'
            def imageName = project.dockerImageName ?: project.name
            def containerName = project.containerName ?: "${project.name}_container"
            def hostPort = project.port ?: 3000
            def containerPort = project.containerPort ?: 80
            def envVars = project.envType == 'inline' ? project.envVariables : [:]
            def envLines = "    IMAGE_NAME = '${quote(imageName)}'\n    CONTAINER_NAME = '${quote(containerName)}'\n"
            envVars?.each { k, v -> envLines += "    ${k} = '${quote(v)}'\n" }

            def pipelineScript = """pipeline {
  agent any
  environment {
${envLines}  }
  stages {
    stage('Updating the source code') {
      steps {
        script {
          echo "Checking out latest code from SCM..."
          def gitCheck = sh(script: "git ls-remote ${quote(project.repoUrl)} ${quote(branch)}", returnStatus: true)
          if (gitCheck != 0) {
            error "Git branch '${quote(branch)}' not found or repo unreachable!"
          }
          checkout([\$class: 'GitSCM', branches: [[name: '${quote(branch)}']], userRemoteConfigs: [[url: '${quote(project.repoUrl)}']]])
          echo "Code update completed."
        }
      }
    }

    stage('Clean Old Image') {
      steps {
        script {
          echo "Checking for existing Docker image..."
          def imgStatus = sh(script: "docker image inspect ${IMAGE_NAME} > /dev/null 2>&1", returnStatus: true)
          if (imgStatus == 0) {
            echo "Image exists. Removing..."
            sh "docker rmi -f ${IMAGE_NAME} || true"
          } else {
            echo "No old image found. Skipping."
          }
        }
      }
    }

    stage('Build Docker Image') {
      steps {
        script {
          echo "Building Docker image '${IMAGE_NAME}'..."
          def buildStatus = sh(script: "docker build -t ${IMAGE_NAME} .", returnStatus: true)
          if (buildStatus != 0) {
            error "Docker build failed!"
          }
          echo "Docker image build completed successfully."
        }
      }
    }

    stage('Scan with Trivy') {
      steps {
        script {
          echo "Scanning Docker image with Trivy..."
          sh "trivy image -f json -o trivy-report.json ${IMAGE_NAME} || true"
          archiveArtifacts artifacts: 'trivy-report.json', fingerprint: true
          def trivyStatus = sh(script: "trivy image --exit-code 1 --severity HIGH,CRITICAL --no-progress ${IMAGE_NAME}", returnStatus: true)
          if (trivyStatus != 0) {
            error "Trivy found HIGH/CRITICAL vulnerabilities!"
          } else {
            echo "No HIGH/CRITICAL vulnerabilities found."
          }
        }
      }
    }

    stage('Remove Existing Container') {
      steps {
        script {
          echo "Checking for existing container..."
          def containerExists = sh(script: "docker ps -aq -f name=${CONTAINER_NAME}", returnStdout: true).trim()
          if (containerExists) {
            echo "Stopping existing container '${CONTAINER_NAME}'..."
            sh "docker stop ${CONTAINER_NAME} || true"
            echo "Removing container '${CONTAINER_NAME}'..."
            sh "docker rm -f ${CONTAINER_NAME} || true"
          } else {
            echo "No existing container found."
          }
        }
      }
    }

    stage('Deploy Container') {
      steps {
        script {
          echo "Deploying Docker container '${CONTAINER_NAME}'..."
          def runStatus = sh(script: "docker run -d -p ${hostPort}:${containerPort} --name ${CONTAINER_NAME} --restart always ${IMAGE_NAME}", returnStatus: true)
          if (runStatus != 0) {
            error "Failed to start Docker container!"
          }
          echo "Docker container deployed successfully."
        }
      }
    }
  }
}"""

            def jobDslText = """pipelineJob('${quote(jobName)}') {
  description('Auto-created pipeline job for ${quote(project.name)}')
  definition {
    cps {
      script('''${pipelineScript}''')
      sandbox()
    }
  }
}"""

            jobDsl scriptText: jobDslText, ignoreExisting: true, removedJobAction: 'IGNORE'
            echo "Processed project ${project.name}, job ${jobName}."
          }
        }
      }
    }
  }

  post {
    success {
      echo '✅ Jenkins job creation pipeline completed successfully.'
    }
    failure {
      echo '❌ Jenkins job creation pipeline failed.'
    }
  }
}
