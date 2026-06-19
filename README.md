# Jenkins Multi-Repo Docker Pipeline

This repository contains a Jenkins pipeline project for building and deploying multiple Git repositories as Docker containers.

## What this project does

- Stores repository configurations in `projects.json`
- Exposes a Jenkins pipeline in `Jenkinsfile`
- Builds Docker images from each configured repository
- Deploys containers using `scripts/deploy.sh`
- Allows adding, listing, and removing project definitions with `scripts/manage_projects.py`

## Project configuration

The `projects.json` file contains project entries with:

- `name`: project identifier
- `repoUrl`: Git repository URL
- `port`: host port for deployment
- `containerPort`: container port to map to the host port
- `environment`: deployment environment label
- `dockerImageName`: Docker image name prefix
- `envVariables`: optional environment variables to inject during deployment

## Jenkins setup

1. Create a Pipeline job in Jenkins.
2. Point the job to this Git repository.
3. Use the default `Jenkinsfile` from the repo.
4. Enable `Build with Parameters`.

### Recommended Jenkins plugins

- Pipeline
- Git
- Docker Pipeline
- Plain Credentials (optional)

> Docker images are built locally on the Jenkins agent and are not pushed to any public registry.

## Using the pipeline

### Build all configured projects

Use `ACTION=build` and leave `PROJECT_NAME` blank.

### Build and deploy a single project

Provide:

- `PROJECT_NAME`
- `ACTION=build-and-deploy`
- Optional `PORT` or `CONTAINER_PORT` overrides
- Optional `ENVIRONMENT`
- Optional `SKIP_SCAN` to skip Trivy scanning
- Optional `ALLOW_SCAN_EXCEPTION` to continue despite HIGH/CRITICAL Trivy findings

## Manage configured repos

Add a repo:

```bash
./scripts/manage_projects.py add --name my-app --repo-url https://github.com/my-org/my-app.git --port 8081 --container-port 3000 --environment staging --docker-image-name my-app --env APP_MODE=production
```

List repos:

```bash
./scripts/manage_projects.py list
```

Remove a repo:

```bash
./scripts/manage_projects.py remove --name my-app
```

## Notes

- Each target repository must include a `Dockerfile` at its root.
- Deployment is performed on the Jenkins agent where Docker is installed.
- If you want to deploy to a remote host, replace `scripts/deploy.sh` with a remote deployment script or SSH-based command.
