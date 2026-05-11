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
export TRASHBOT_REMOTE_CLOUD_PUBLIC_BASE_URL="${TRASHBOT_REMOTE_CLOUD_PUBLIC_BASE_URL:-http://127.0.0.1:${PORT}}"
export TRASHBOT_REMOTE_CLOUD_TLS_MODE="${TRASHBOT_REMOTE_CLOUD_TLS_MODE:-future_reverse_proxy}"
export TRASHBOT_REMOTE_CLOUD_PUBLIC_INGRESS="${TRASHBOT_REMOTE_CLOUD_PUBLIC_INGRESS:-missing}"
export TRASHBOT_REMOTE_CLOUD_OSS_BUCKET="${TRASHBOT_REMOTE_CLOUD_OSS_BUCKET:-bytegallop}"
export TRASHBOT_REMOTE_CLOUD_OSS_REGION="${TRASHBOT_REMOTE_CLOUD_OSS_REGION:-oss-cn-hangzhou}"
export TRASHBOT_REMOTE_CLOUD_OSS_PREFIX="${TRASHBOT_REMOTE_CLOUD_OSS_PREFIX:-rober/<robot_id>/<date>/<task_id>/}"
export TRASHBOT_REMOTE_CLOUD_CDN_BASE_URL="${TRASHBOT_REMOTE_CLOUD_CDN_BASE_URL:-https://cdn.bytegallop.com/rober/}"
export TRASHBOT_REMOTE_CLOUD_OSS_CREDENTIAL_MODE="${TRASHBOT_REMOTE_CLOUD_OSS_CREDENTIAL_MODE:-placeholder}"
export TRASHBOT_REMOTE_CLOUD_STATE_BACKEND="${TRASHBOT_REMOTE_CLOUD_STATE_BACKEND:-file}"

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

echo "== production preflight endpoint expects Docker/local blocked =="
set +e
PREFLIGHT_HTTP="$(curl -sS -o /tmp/remote_cloud_relay_preflightz.json -w "%{http_code}" "${BASE_URL}/preflightz")"
set -e
cat /tmp/remote_cloud_relay_preflightz.json
echo
if [ "${PREFLIGHT_HTTP}" != "503" ]; then
  echo "preflightz unexpectedly returned ${PREFLIGHT_HTTP}" >&2
  exit 1
fi
python3 - /tmp/remote_cloud_relay_preflightz.json <<'PY'
import json
import sys

payload = json.load(open(sys.argv[1], encoding="utf-8"))
encoded = json.dumps(payload, ensure_ascii=False)
required = (
    "software_proof_docker_preflight_gate",
    "missing_or_placeholder_credential",
    "https_public_ingress_missing",
    "oss_cdn_not_production_ready",
)
for marker in required:
    if marker not in encoded:
        raise SystemExit(f"missing preflight marker: {marker}")
for forbidden in ("Authorization", "Bearer", "/cmd_vel", "ttyUSB", "baudrate", "WAVE ROVER"):
    if forbidden in encoded:
        raise SystemExit(f"preflight leaked forbidden marker: {forbidden}")
if payload.get("production_ready"):
    raise SystemExit("preflight must not pass for Docker/local placeholder config")
PY

echo "== production preflight CLI with unwritable state expects blocked =="
set +e
TRASHBOT_REMOTE_CLOUD_STATE=/dev/null/relay_state.json \
PYTHONPATH=src/ros2_trashbot_behavior \
python3 -m ros2_trashbot_behavior.remote_cloud_relay --preflight >/tmp/remote_cloud_relay_preflight_cli.json
PREFLIGHT_CLI_STATUS="$?"
set -e
cat /tmp/remote_cloud_relay_preflight_cli.json
echo
if [ "${PREFLIGHT_CLI_STATUS}" != "2" ]; then
  echo "preflight CLI unexpectedly returned ${PREFLIGHT_CLI_STATUS}" >&2
  exit 1
fi
python3 - /tmp/remote_cloud_relay_preflight_cli.json <<'PY'
import json
import sys

payload = json.load(open(sys.argv[1], encoding="utf-8"))
checks = {check["name"]: check for check in payload.get("checks", [])}
if checks.get("state_store", {}).get("code") != "state_store_not_writable":
    raise SystemExit("unwritable state store was not reported as blocked")
if payload.get("evidence_boundary") != "software_proof_docker_preflight_gate":
    raise SystemExit("wrong evidence boundary")
PY

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
