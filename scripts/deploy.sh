#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 5 ]; then
  echo "Usage: $0 <container-name> <image-tag> <host-port> <container-port> <environment> [env-file]"
  exit 1
fi

container_name="$1"
image_tag="$2"
host_port="$3"
container_port="$4"
environment="$5"
env_file="${6:-}"

existing=$(docker ps -aq --filter "name=^/${container_name}$")
if [ -n "$existing" ]; then
  echo "Stopping and removing existing container ${container_name}"
  docker rm -f "$existing"
fi

cmd=(docker run -d --name "$container_name" -p "${host_port}:${container_port}" -e ENVIRONMENT="$environment" --restart always "$image_tag")

if [ -n "$env_file" ] && [ -f "$env_file" ]; then
  while IFS='=' read -r key value; do
    if [ -n "$key" ] && [ -n "$value" ]; then
      cmd+=( -e "$key=$value" )
    fi
  done < <(grep -v '^#' "$env_file" | sed '/^[[:space:]]*$/d')
elif [ -f ".env" ]; then
  while IFS='=' read -r key value; do
    if [ -n "$key" ] && [ -n "$value" ]; then
      cmd+=( -e "$key=$value" )
    fi
  done < <(grep -v '^#' .env | sed '/^[[:space:]]*$/d')
fi

echo "Running: ${cmd[*]}"
"${cmd[@]}"
