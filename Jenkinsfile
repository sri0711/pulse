pipeline {
  agent any

  triggers {
    cron('H * * * *')
  }


  stages {
    stage('Show configured projects') {
      steps {
        script {
          def configText = readFile('projects.json')
          def toSerializable
          toSerializable = { obj ->
            if (obj instanceof Map) {
              def result = new java.util.HashMap()
              obj.each { k, v -> result[k] = toSerializable(v) }
              return result
            }
            if (obj instanceof Collection) {
              return obj.collect { toSerializable(it) }
            }
            return obj
          }
          def projects = toSerializable(new groovy.json.JsonSlurper().parseText(configText))
          echo "Configured projects:"
          projects.each { project ->
            echo "- ${project.name} -> ${project.repoUrl} on host port ${project.port} container port ${project.containerPort ?: 80} env ${project.environment}"
          }
          echo 'Pipeline will process all projects configured in projects.json.'
        }
      }
    }

    stage('Process projects') {
      steps {
        script {
          def configText = readFile('projects.json')
          def toSerializable
          toSerializable = { obj ->
            if (obj instanceof Map) {
              def result = new java.util.HashMap()
              obj.each { k, v -> result[k] = toSerializable(v) }
              return result
            }
            if (obj instanceof Collection) {
              return obj.collect { toSerializable(it) }
            }
            return obj
          }
          def projects = toSerializable(new groovy.json.JsonSlurper().parseText(configText))
          def selected = projects
          if (!selected) {
            error 'No projects configured in projects.json.'
          }

          selected.each { project ->
            def repoUrl = project.repoUrl
            def branch = project.gitBranch ?: 'main'
            def hostPort = project.port.toString()
            def containerPort = (project.containerPort ?: 80).toString()
            def imageName = project.dockerImageName ?: project.name
            def imageTag = "${imageName}:${env.BUILD_NUMBER ?: 'latest'}"
            def deployEnv = project.environment
            def containerName = "${project.name}-${deployEnv}"
            def envFile = ''

            echo "=== Update source code: ${project.name} ==="
            echo "Checking repo ${repoUrl} branch ${branch}"
            def gitCheck = sh(script: "git ls-remote --exit-code ${repoUrl} ${branch}", returnStatus: true)
            if (gitCheck != 0) {
              error "Git branch '${branch}' not found or repo unreachable!"
            }
            sh 'rm -rf target-repo'
            sh "git clone --branch ${branch} --depth 1 ${repoUrl} target-repo"

            echo "=== Clean Old Image: ${project.name} ==="
            echo "Checking for existing Docker image ${imageName}..."
            def imgStatus = sh(script: "docker image inspect ${imageName} > /dev/null 2>&1", returnStatus: true)
            if (imgStatus == 0) {
              echo "Image exists. Removing ${imageName}..."
              sh "docker rmi -f ${imageName} || true"
            } else {
              echo "No old image found. Skipping."
            }

            echo "=== Build Docker Image: ${project.name} ==="
            echo "Building Docker image '${imageTag}'..."
            def buildStatus = sh(script: "cd target-repo && docker build -t ${imageTag} .", returnStatus: true)
            if (buildStatus != 0) {
              error "Docker build failed!"
            }
            echo "Docker image build completed successfully."

            echo "=== Scan with Trivy: ${project.name} ==="
            def scanEnabled = project.containsKey('scanEnabled') ? project.scanEnabled : true
            def scanException = project.containsKey('scanException') ? project.scanException : false
            def effectiveSkipScan = !scanEnabled
            def effectiveAllowException = scanException

            if (effectiveSkipScan) {
              echo "Skipping Trivy scan for ${project.name}."
            } else {
              echo "Scanning Docker image with Trivy..."
              def reportFile = "trivy-report-${project.name}.json"
              sh "trivy image -f json -o ${reportFile} ${imageTag} || true"
              archiveArtifacts artifacts: reportFile, fingerprint: true

              def trivyStatus = sh(script: "trivy image --exit-code 1 --severity HIGH,CRITICAL --no-progress ${imageTag}", returnStatus: true)
              if (trivyStatus != 0) {
                if (effectiveAllowException) {
                  echo "WARNING: Trivy found HIGH/CRITICAL vulnerabilities, but scan exception is enabled. Continuing."
                } else {
                  error "Trivy found HIGH/CRITICAL vulnerabilities!"
                }
              } else {
                echo "No HIGH/CRITICAL vulnerabilities found."
              }
            }

            echo "=== Remove Existing Container: ${project.name} ==="
            echo "Checking for existing container ${containerName}..."
            def containerExists = sh(script: "docker ps -aq -f name=${containerName}", returnStdout: true).trim()
            if (containerExists) {
              echo "Stopping existing container '${containerName}'..."
              sh "docker stop ${containerName} || true"
              echo "Removing container '${containerName}'..."
              sh "docker rm -f ${containerName} || true"
            } else {
              echo "No existing container found."
            }

            echo "=== Deploy Container: ${project.name} ==="
            def envFilePath = ''
            if (project.envType == 'file' && project.envFile) {
              envFilePath = "env/${project.envFile}"
              if (!fileExists(envFilePath)) {
                error "Env file ${envFilePath} not found for project ${project.name}."
              }
              echo "Loading environment from ${envFilePath}"
            } else if (fileExists("env/${project.name}.env")) {
              envFilePath = "env/${project.name}.env"
              echo "Loading environment from ${envFilePath}"
            } else if (project.envType != 'file' && project.envVariables) {
              envFilePath = 'target-repo/jenkins.env'
              writeFile file: envFilePath, text: project.envVariables.collect { k, v -> "${k}=${v}" }.join('\n')
              echo "Using inline envVariables for ${project.name}."
            }

            echo "Deploying Docker container '${containerName}'..."
            def deployCmd = "./scripts/deploy.sh ${containerName} ${imageTag} ${hostPort} ${containerPort} ${deployEnv}"
            if (envFilePath) {
              deployCmd += " ${envFilePath}"
            }
            def runStatus = sh(script: deployCmd, returnStatus: true)
            if (runStatus != 0) {
              error "Failed to start Docker container!"
            }
            echo "Docker container deployed successfully."
          }
        }
      }
    }
  }

  post {
    success {
      echo '✅ Docker image built, scanned, and deployed successfully!'
    }
    failure {
      echo '❌ Build failed due to errors or vulnerabilities.'
    }
  }
}
