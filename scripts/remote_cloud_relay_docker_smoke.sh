#!/usr/bin/env bash
set -euo pipefail

# 这个 smoke 只验证 Docker deploy proof，不声明真实云、4G、TLS、OSS/CDN 或 HIL。
PROJECT_NAME="${PROJECT_NAME:-ros-rbs-remote-cloud-relay-smoke}"
PORT="${TRASHBOT_REMOTE_CLOUD_PUBLISHED_PORT:-18088}"
TOKEN="${TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN:-dev-smoke-token}"
BASE_URL="http://127.0.0.1:${PORT}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.remote-cloud-relay.yml}"

export TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN="${TOKEN}"
export TRASHBOT_REMOTE_CLOUD_PUBLISHED_PORT="${PORT}"
export TRASHBOT_REMOTE_CLOUD_PORT="${TRASHBOT_REMOTE_CLOUD_PORT:-8088}"
export TRASHBOT_REMOTE_CLOUD_HOST="${TRASHBOT_REMOTE_CLOUD_HOST:-0.0.0.0}"
export TRASHBOT_REMOTE_CLOUD_STATE="${TRASHBOT_REMOTE_CLOUD_STATE:-/data/remote_cloud_relay_state.json}"

cleanup() {
  # 保留 docker logs 输出在调用方日志中，最后清理容器避免影响后续 sprint。
  docker compose -p "${PROJECT_NAME}" -f "${COMPOSE_FILE}" logs --no-color remote-cloud-relay || true
  docker compose -p "${PROJECT_NAME}" -f "${COMPOSE_FILE}" down --volumes --remove-orphans || true
}
trap cleanup EXIT

echo "== build image =="
docker compose -p "${PROJECT_NAME}" -f "${COMPOSE_FILE}" build remote-cloud-relay

echo "== start relay container =="
docker compose -p "${PROJECT_NAME}" -f "${COMPOSE_FILE}" up -d remote-cloud-relay

echo "== wait for readiness =="
READY_OK=0
for _ in $(seq 1 20); do
  if curl -fsS "${BASE_URL}/readyz" >/tmp/remote_cloud_relay_readyz.json; then
    cat /tmp/remote_cloud_relay_readyz.json
    echo
    READY_OK=1
    break
  fi
  sleep 1
done
if [ "${READY_OK}" != "1" ]; then
  echo "readyz did not become healthy" >&2
  exit 1
fi

echo "== healthz =="
curl -fsS "${BASE_URL}/healthz"
echo

echo "== post status =="
NOW="$(python3 - <<'PY'
import time
print(time.time())
PY
)"
curl -fsS \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"protocol_version":"trashbot.remote.v1","state":"idle","message":"docker smoke status","updated_at":'"${NOW}"',"diagnostics":{"network":"docker_deploy_smoke"}}' \
  "${BASE_URL}/robots/trashbot-001/status"
echo

echo "== enqueue command =="
curl -fsS \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"protocol_version":"trashbot.remote.v1","id":"cmd-docker-smoke-1","type":"collect","expires_at":2778256300.0,"payload":{"target":"trash_station","trash_type":0}}' \
  "${BASE_URL}/robots/trashbot-001/commands"
echo

echo "== robot get next command =="
curl -fsS \
  -H "Authorization: Bearer ${TOKEN}" \
  "${BASE_URL}/robots/trashbot-001/commands/next?last_ack_id="
echo

echo "== post ack =="
curl -fsS \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"protocol_version":"trashbot.remote.v1","state":"acked","message":"docker smoke ack","updated_at":'"${NOW}"',"result":{"bridge":"submitted"}}' \
  "${BASE_URL}/robots/trashbot-001/commands/cmd-docker-smoke-1/ack"
echo

echo "== read ack =="
curl -fsS \
  -H "Authorization: Bearer ${TOKEN}" \
  "${BASE_URL}/robots/trashbot-001/commands/cmd-docker-smoke-1/ack"
echo

echo "== read status =="
curl -fsS \
  -H "Authorization: Bearer ${TOKEN}" \
  "${BASE_URL}/robots/trashbot-001/status"
echo
