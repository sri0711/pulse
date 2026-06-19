# Jenkins pipeline job creator

This repository now contains a Jenkins pipeline that only creates new Jenkins pipeline jobs from the `projects.json` file.

## What this repository does

- Reads `projects.json`
- Creates a Jenkins pipeline job for each project entry
- If a job already exists, it is ignored
- Runs every hour via Jenkins cron trigger

## Jenkins setup

1. Create a Pipeline job in Jenkins.
2. Point the job to this Git repository.
3. Use the default `Jenkinsfile` from the repo.
4. Ensure the job is allowed to run shell scripts and Python.

## Project configuration

Add project definitions in `projects.json`, for example:

```json
[
	{
		"name": "orchestra",
		"repoUrl": "https://github.com/sri0711/orchestra.git",
		"gitBranch": "main",
		"envType": "inline",
		"envVariables": {
			"APP_ENV": "prod"
		}
	}
]
```

### If the pipeline exists

- Existing Jenkins jobs are skipped.
- Only new jobs are created.

## Job creation

The Jenkins job uses native Jenkins pipeline logic to:

- read `projects.json`
- create pipeline jobs for new projects
- ignore jobs that already exist

## Requirements

- Jenkins Job DSL plugin installed
- Pipeline Utility Steps plugin is not required
- No external Python script is needed

## Notes

- This pipeline does not build Docker images.
- It only creates Jenkins jobs from configured projects.
