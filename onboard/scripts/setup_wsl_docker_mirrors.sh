#!/usr/bin/env bash
# Configure Docker Engine registry mirrors for WSL/Linux.
set -euo pipefail

daemon_file="${DOCKER_DAEMON_JSON:-/etc/docker/daemon.json}"
mirrors="${DOCKER_REGISTRY_MIRRORS:-https://docker.m.daocloud.io,https://docker.1ms.run,https://docker.1panel.live}"

if ! command -v docker >/dev/null 2>&1; then
    echo "docker command is not available. Install Docker Desktop with WSL integration or Docker Engine first." >&2
    exit 2
fi

if [ "$(id -u)" -ne 0 ]; then
    exec sudo DOCKER_DAEMON_JSON="$daemon_file" DOCKER_REGISTRY_MIRRORS="$mirrors" bash "$0"
fi

tmp_file="$(mktemp)"
trap 'rm -f "$tmp_file"' EXIT

IFS=',' read -r -a mirror_array <<< "$mirrors"
{
    echo '{'
    echo '  "registry-mirrors": ['
    for i in "${!mirror_array[@]}"; do
        mirror="${mirror_array[$i]}"
        comma=","
        if [ "$i" -eq "$((${#mirror_array[@]} - 1))" ]; then
            comma=""
        fi
        printf '    "%s"%s\n' "$mirror" "$comma"
    done
    echo '  ]'
    echo '}'
} > "$tmp_file"

install -d "$(dirname "$daemon_file")"
install -m 0644 "$tmp_file" "$daemon_file"

if command -v systemctl >/dev/null 2>&1 && systemctl is-system-running >/dev/null 2>&1; then
    systemctl restart docker
else
    service docker restart || true
fi

echo "Docker registry mirrors written to $daemon_file"
docker info 2>/dev/null | sed -n '/Registry Mirrors/,+8p' || true
