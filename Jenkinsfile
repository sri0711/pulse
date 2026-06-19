pipeline {
  agent any

  triggers {
    cron('H * * * *')
  }

  parameters {
    string(name: 'PROJECT_NAME', defaultValue: '', description: 'Project name from projects.json. Leave blank to build/deploy all projects.')
    string(name: 'REPO_URL', defaultValue: '', description: 'Optional override repository URL for the selected project.')
    string(name: 'GIT_BRANCH', defaultValue: 'main', description: 'Branch to build from.')
    string(name: 'CREDENTIALS_ID', defaultValue: '', description: 'Optional Jenkins credentials ID for private repo access.')
    string(name: 'PORT', defaultValue: '', description: 'Optional override host port mapping for the container.')
    string(name: 'CONTAINER_PORT', defaultValue: '', description: 'Optional override container port. Defaults to project config or 80.')
    choice(name: 'ACTION', choices: ['build', 'deploy', 'build-and-deploy'], description: 'Pipeline action to perform.')
    choice(name: 'ENVIRONMENT', choices: ['dev', 'staging', 'prod'], description: 'Deployment environment variable.')
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
          if (!params.PROJECT_NAME?.trim()) {
            echo 'No PROJECT_NAME selected; pipeline will process all configured projects.'
          } else {
            echo "Selected project: ${params.PROJECT_NAME}"
          }
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
          def selected = []

          if (params.PROJECT_NAME?.trim()) {
            selected = projects.findAll { it.name == params.PROJECT_NAME.trim() }
          } else {
            selected = projects
          }

          if (!selected) {
            error "No project found matching PROJECT_NAME='${params.PROJECT_NAME}'. Check projects.json or use list mode."
          }

          selected.each { project ->
            def repoUrl = params.REPO_URL?.trim() ?: project.repoUrl
            def branch = params.GIT_BRANCH?.trim() ?: 'main'
            def hostPort = params.PORT?.trim() ?: project.port.toString()
            def containerPort = params.CONTAINER_PORT?.trim() ?: (project.containerPort ?: 80).toString()
            def imageName = project.dockerImageName ?: project.name
            def imageTag = "${imageName}:${env.BUILD_NUMBER ?: 'latest'}"
            def deployEnv = params.ENVIRONMENT?.trim() ?: project.environment
            def containerName = "${project.name}-${deployEnv}"
            def envFile = ''

            stage("Update source code: ${project.name}") {
              script {
                echo "Checking repo ${repoUrl} branch ${branch}"
                def gitCheck = sh(script: "git ls-remote --exit-code ${repoUrl} ${branch}", returnStatus: true)
                if (gitCheck != 0) {
                  error "Git branch '${branch}' not found or repo unreachable!"
                }

                sh 'rm -rf target-repo'
                sh "git clone --branch ${branch} --depth 1 ${repoUrl} target-repo"
              }
            }

            stage("Clean Old Image: ${project.name}") {
              steps {
                script {
                  echo "Checking for existing Docker image ${imageName}..."
                  def imgStatus = sh(script: "docker image inspect ${imageName} > /dev/null 2>&1", returnStatus: true)
                  if (imgStatus == 0) {
                    echo "Image exists. Removing ${imageName}..."
                    sh "docker rmi -f ${imageName} || true"
                  } else {
                    echo "No old image found. Skipping."
                  }
                }
              }
            }

            stage("Build Docker Image: ${project.name}") {
              steps {
                script {
                  echo "Building Docker image '${imageTag}'..."
                  def buildStatus = sh(script: "cd target-repo && docker build -t ${imageTag} .", returnStatus: true)
                  if (buildStatus != 0) {
                    error "Docker build failed!"
                  }
                  echo "Docker image build completed successfully."
                }
              }
            }

            stage("Scan with Trivy: ${project.name}") {
              steps {
                script {
                  echo "Scanning Docker image with Trivy..."
                  def reportFile = "trivy-report-${project.name}.json"
                  sh "trivy image -f json -o ${reportFile} ${imageTag} || true"
                  archiveArtifacts artifacts: reportFile, fingerprint: true

                  def trivyStatus = sh(script: "trivy image --exit-code 1 --severity HIGH,CRITICAL --no-progress ${imageTag}", returnStatus: true)
                  if (trivyStatus != 0) {
                    error "Trivy found HIGH/CRITICAL vulnerabilities!"
                  } else {
                    echo "No HIGH/CRITICAL vulnerabilities found."
                  }
                }
              }
            }

            stage("Remove Existing Container: ${project.name}") {
              steps {
                script {
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
                }
              }
            }

            stage("Deploy Container: ${project.name}") {
              steps {
                script {
                  def envFilePath = ''
                  def envDirFile = "env/${project.name}.env"

                  if (fileExists(envDirFile)) {
                    echo "Loading environment from ${envDirFile}"
                    envFilePath = envDirFile
                  } else if (project.envVariables) {
                    envFilePath = 'target-repo/jenkins.env'
                    writeFile file: envFilePath, text: project.envVariables.collect { k, v -> "${k}=${v}" }.join('\n')
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
