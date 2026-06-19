#!/usr/bin/env python3
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECTS_FILE = os.path.join(ROOT, 'projects.json')


def load_projects():
    if not os.path.exists(PROJECTS_FILE):
        return []
    with open(PROJECTS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_projects(projects):
    with open(PROJECTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(projects, f, indent=2)


def parse_env_pairs(env_pairs):
    env = {}
    for pair in env_pairs or []:
        if '=' not in pair:
            raise ValueError(f'Invalid env variable: {pair}. Use KEY=VALUE')
        key, value = pair.split('=', 1)
        env[key.strip()] = value.strip()
    return env


def add_project(args):
    projects = load_projects()
    if any(p['name'] == args.name for p in projects):
        print(f"Project with name '{args.name}' already exists.")
        sys.exit(1)

    project = {
        'name': args.name,
        'repoUrl': args.repo_url,
        'port': int(args.port),
        'containerPort': int(args.container_port) if args.container_port else 80,
        'environment': args.environment,
        'dockerImageName': args.image_name or args.name,
        'envVariables': parse_env_pairs(args.env or [])
    }
    projects.append(project)
    save_projects(projects)
    print(f"Added project '{args.name}' to projects.json.")


def list_projects(_args):
    projects = load_projects()
    if not projects:
        print('No projects configured in projects.json.')
        return
    for project in projects:
        print(f"- {project['name']}")
        print(f"  repoUrl: {project['repoUrl']}")
        print(f"  port: {project['port']}")
        print(f"  containerPort: {project.get('containerPort', 80)}")
        print(f"  environment: {project['environment']}")
        print(f"  dockerImageName: {project['dockerImageName']}")
        if project.get('envVariables'):
            print('  envVariables:')
            for k, v in project['envVariables'].items():
                print(f"    {k}={v}")


def remove_project(args):
    projects = load_projects()
    filtered = [p for p in projects if p['name'] != args.name]
    if len(filtered) == len(projects):
        print(f"Project '{args.name}' not found.")
        sys.exit(1)
    save_projects(filtered)
    print(f"Removed project '{args.name}' from projects.json.")


def main():
    parser = argparse.ArgumentParser(description='Manage repos for Jenkins Docker pipeline.')
    subparsers = parser.add_subparsers(dest='command', required=True)

    add = subparsers.add_parser('add', help='Add a new project to projects.json')
    add.add_argument('--name', required=True)
    add.add_argument('--repo-url', required=True)
    add.add_argument('--port', required=True)
    add.add_argument('--container-port', default='80')
    add.add_argument('--environment', default='dev')
    add.add_argument('--docker-image-name', dest='image_name')
    add.add_argument('--env', nargs='*', help='Additional env variables in KEY=VALUE form.')
    add.set_defaults(func=add_project)

    list_cmd = subparsers.add_parser('list', help='List configured projects')
    list_cmd.set_defaults(func=list_projects)

    rm = subparsers.add_parser('remove', help='Remove a configured project')
    rm.add_argument('--name', required=True)
    rm.set_defaults(func=remove_project)

    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
