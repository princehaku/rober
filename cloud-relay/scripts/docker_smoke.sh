#!/usr/bin/env bash
set -euo pipefail

# 本脚本位于 cloud-relay/scripts/；compose 与 Dockerfile 均在 cloud-relay/ 下，默认在此目录执行 docker compose。
relay_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$relay_root"

# 这个 smoke 只验证 Docker deploy proof，不声明真实云、4G、TLS、OSS/CDN 或 HIL。
PROJECT_NAME="${PROJECT_NAME:-ros-rbs-remote-cloud-relay-smoke}"
PORT="${TRASHBOT_REMOTE_CLOUD_PUBLISHED_PORT:-18088}"
TOKEN="${TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN:-dev-smoke-token}"
BASE_URL="http://127.0.0.1:${PORT}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"

export TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN="${TOKEN}"
export TRASHBOT_REMOTE_CLOUD_PUBLISHED_PORT="${PORT}"
export TRASHBOT_REMOTE_CLOUD_PORT="${TRASHBOT_REMOTE_CLOUD_PORT:-8088}"
export TRASHBOT_REMOTE_CLOUD_HOST="${TRASHBOT_REMOTE_CLOUD_HOST:-0.0.0.0}"
export TRASHBOT_REMOTE_CLOUD_STATE_BACKEND="${TRASHBOT_REMOTE_CLOUD_STATE_BACKEND:-sqlite}"
if [ "${TRASHBOT_REMOTE_CLOUD_STATE_BACKEND}" = "sqlite" ]; then
  export TRASHBOT_REMOTE_CLOUD_STATE="${TRASHBOT_REMOTE_CLOUD_STATE:-/data/remote_cloud_relay_state.sqlite}"
else
  export TRASHBOT_REMOTE_CLOUD_STATE="${TRASHBOT_REMOTE_CLOUD_STATE:-/data/remote_cloud_relay_state.json}"
fi
export TRASHBOT_REMOTE_CLOUD_PUBLIC_BASE_URL="${TRASHBOT_REMOTE_CLOUD_PUBLIC_BASE_URL:-http://127.0.0.1:${PORT}}"
export TRASHBOT_REMOTE_CLOUD_TLS_MODE="${TRASHBOT_REMOTE_CLOUD_TLS_MODE:-future_reverse_proxy}"
export TRASHBOT_REMOTE_CLOUD_PUBLIC_INGRESS="${TRASHBOT_REMOTE_CLOUD_PUBLIC_INGRESS:-missing}"
export TRASHBOT_REMOTE_CLOUD_DB_CONFIG="${TRASHBOT_REMOTE_CLOUD_DB_CONFIG:-missing}"
export TRASHBOT_REMOTE_CLOUD_QUEUE_CONFIG="${TRASHBOT_REMOTE_CLOUD_QUEUE_CONFIG:-missing}"
export TRASHBOT_REMOTE_CLOUD_DB_MIGRATION_CONFIG="${TRASHBOT_REMOTE_CLOUD_DB_MIGRATION_CONFIG:-missing}"
export TRASHBOT_REMOTE_CLOUD_QUEUE_WORKER_CONFIG="${TRASHBOT_REMOTE_CLOUD_QUEUE_WORKER_CONFIG:-missing}"
export TRASHBOT_REMOTE_CLOUD_OSS_BUCKET="${TRASHBOT_REMOTE_CLOUD_OSS_BUCKET:-bytegallop}"
export TRASHBOT_REMOTE_CLOUD_OSS_REGION="${TRASHBOT_REMOTE_CLOUD_OSS_REGION:-oss-cn-hangzhou}"
export TRASHBOT_REMOTE_CLOUD_OSS_PREFIX="${TRASHBOT_REMOTE_CLOUD_OSS_PREFIX:-rober/<robot_id>/<date>/<task_id>/}"
export TRASHBOT_REMOTE_CLOUD_CDN_BASE_URL="${TRASHBOT_REMOTE_CLOUD_CDN_BASE_URL:-https://cdn.bytegallop.com/rober/}"
export TRASHBOT_REMOTE_CLOUD_OSS_CREDENTIAL_MODE="${TRASHBOT_REMOTE_CLOUD_OSS_CREDENTIAL_MODE:-placeholder}"

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
    "software_proof_docker_cloud_db_queue_config_gate",
    "software_proof_docker_cloud_public_ingress_tls_gate",
    "cloud_deployment_readiness",
    "cloud_public_ingress_tls",
    "cloud_db_queue_config",
    "missing_cloud_db_queue_config",
    "missing_public_ingress_tls_config",
    "missing_or_placeholder_credential",
    "https_public_ingress_missing",
    "oss_cdn_not_production_ready",
    "sqlite_state_store_proof_only",
    "production_db_or_queue",
    "multi_instance_consistency",
    "backup_restore",
    "disaster_recovery",
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

echo "== cloud DB/queue config gate distinguishes missing config =="
docker compose -p "${PROJECT_NAME}" -f "${COMPOSE_FILE}" exec -T remote-cloud-relay \
  rm -f /tmp/trashbot_cloud_db_queue_config_missing.json
docker compose -p "${PROJECT_NAME}" -f "${COMPOSE_FILE}" exec -T remote-cloud-relay \
  python -m ros2_trashbot_cloud_relay.remote_cloud_relay \
    --write-cloud-db-queue-config-artifact /tmp/trashbot_cloud_db_queue_config_missing.json \
    >/tmp/trashbot_cloud_db_queue_config_missing_result.json
docker compose -p "${PROJECT_NAME}" -f "${COMPOSE_FILE}" exec -T remote-cloud-relay \
  cat /tmp/trashbot_cloud_db_queue_config_missing.json \
    >/tmp/trashbot_cloud_db_queue_config_missing.json
cat /tmp/trashbot_cloud_db_queue_config_missing.json
echo
python3 - /tmp/trashbot_cloud_db_queue_config_missing.json <<'PY'
import json
import sys

payload = json.load(open(sys.argv[1], encoding="utf-8"))
encoded = json.dumps(payload, ensure_ascii=False)
if payload.get("schema") != "trashbot.cloud_db_queue_config_gate":
    raise SystemExit("wrong cloud DB/queue config schema")
if payload.get("evidence_boundary") != "software_proof_docker_cloud_db_queue_config_gate":
    raise SystemExit("wrong cloud DB/queue config evidence boundary")
if payload.get("state") != "missing_cloud_db_queue_config":
    raise SystemExit("missing-config state was not reported")
if payload.get("production_ready") or payload.get("overall_status") != "blocked":
    raise SystemExit("cloud DB/queue config gate must remain production blocked")
for marker in ("production_db_or_queue", "multi_instance_consistency", "production_backup_policy"):
    if marker not in encoded:
        raise SystemExit(f"missing cloud DB/queue config marker: {marker}")
for forbidden in ("Authorization", "Bearer", "postgres://", "mysql://", "redis://", "amqp://", "queue URL", "database URL", "/cmd_vel", "ttyUSB", "baudrate", "WAVE ROVER", "/tmp/"):
    if forbidden in encoded:
        raise SystemExit(f"cloud DB/queue config leaked forbidden marker: {forbidden}")
PY

echo "== cloud DB/queue config gate distinguishes config package without external proof =="
docker compose -p "${PROJECT_NAME}" -f "${COMPOSE_FILE}" exec -T \
  -e TRASHBOT_REMOTE_CLOUD_DB_CONFIG=present \
  -e TRASHBOT_REMOTE_CLOUD_QUEUE_CONFIG=present \
  -e TRASHBOT_REMOTE_CLOUD_DB_MIGRATION_CONFIG=present \
  -e TRASHBOT_REMOTE_CLOUD_QUEUE_WORKER_CONFIG=present \
  remote-cloud-relay \
  python -m ros2_trashbot_cloud_relay.remote_cloud_relay \
    --write-cloud-db-queue-config-artifact /tmp/trashbot_cloud_db_queue_config_present.json \
    >/tmp/trashbot_cloud_db_queue_config_present_result.json
docker compose -p "${PROJECT_NAME}" -f "${COMPOSE_FILE}" exec -T remote-cloud-relay \
  cat /tmp/trashbot_cloud_db_queue_config_present.json \
    >/tmp/trashbot_cloud_db_queue_config_present.json
cat /tmp/trashbot_cloud_db_queue_config_present.json
echo
python3 - /tmp/trashbot_cloud_db_queue_config_present.json <<'PY'
import json
import sys

payload = json.load(open(sys.argv[1], encoding="utf-8"))
encoded = json.dumps(payload, ensure_ascii=False)
if payload.get("state") != "cloud_db_queue_config_present_not_externally_proven":
    raise SystemExit("config-present-not-proven state was not reported")
if not payload.get("config_package_present"):
    raise SystemExit("config package presence was not reported")
if payload.get("external_db_queue_probe_proven"):
    raise SystemExit("external DB/queue proof must remain false")
if payload.get("production_ready") or payload.get("overall_status") != "blocked":
    raise SystemExit("config-present gate must remain production blocked")
for forbidden in ("Authorization", "Bearer", "postgres://", "mysql://", "redis://", "amqp://", "queue URL", "database URL", "/cmd_vel", "ttyUSB", "baudrate", "WAVE ROVER", "/tmp/"):
    if forbidden in encoded:
        raise SystemExit(f"config-present DB/queue gate leaked forbidden marker: {forbidden}")
PY

echo "== production preflight CLI consumes cloud DB/queue config gate without production ready =="
set +e
docker compose -p "${PROJECT_NAME}" -f "${COMPOSE_FILE}" exec -T \
  -e TRASHBOT_REMOTE_CLOUD_DB_QUEUE_CONFIG_ARTIFACT=/tmp/trashbot_cloud_db_queue_config_present.json \
  remote-cloud-relay \
  python -m ros2_trashbot_cloud_relay.remote_cloud_relay --preflight \
  >/tmp/remote_cloud_relay_preflight_cloud_db_queue_config.json
PREFLIGHT_CLOUD_DB_QUEUE_STATUS="$?"
set -e
cat /tmp/remote_cloud_relay_preflight_cloud_db_queue_config.json
echo
if [ "${PREFLIGHT_CLOUD_DB_QUEUE_STATUS}" != "0" ]; then
  echo "cloud DB/queue config preflight CLI unexpectedly returned ${PREFLIGHT_CLOUD_DB_QUEUE_STATUS}" >&2
  exit 1
fi
python3 - /tmp/remote_cloud_relay_preflight_cloud_db_queue_config.json <<'PY'
import json
import sys

payload = json.load(open(sys.argv[1], encoding="utf-8"))
checks = {check["name"]: check for check in payload.get("checks", [])}
encoded = json.dumps(payload, ensure_ascii=False)
if payload.get("production_ready") or payload.get("overall_status") != "blocked":
    raise SystemExit("cloud DB/queue config preflight must remain blocked")
if payload.get("evidence_boundary") != "software_proof_docker_cloud_db_queue_config_gate":
    raise SystemExit("preflight did not report cloud DB/queue config boundary")
if checks.get("cloud_db_queue_config", {}).get("code") != "cloud_db_queue_config_present_not_externally_proven":
    raise SystemExit("preflight did not preserve DB/queue config-present-not-proven state")
if checks.get("cloud_db_queue_config", {}).get("details", {}).get("external_db_queue_probe_proven"):
    raise SystemExit("preflight must not claim external DB/queue proof")
for forbidden in ("Authorization", "Bearer", "postgres://", "mysql://", "redis://", "amqp://", "queue URL", "database URL", "/cmd_vel", "ttyUSB", "baudrate", "WAVE ROVER", "/tmp/"):
    if forbidden in encoded:
        raise SystemExit(f"cloud DB/queue config preflight leaked forbidden marker: {forbidden}")
PY

echo "== cloud public ingress TLS gate distinguishes missing config =="
docker compose -p "${PROJECT_NAME}" -f "${COMPOSE_FILE}" exec -T remote-cloud-relay \
  rm -f /tmp/trashbot_cloud_public_ingress_tls_missing.json
docker compose -p "${PROJECT_NAME}" -f "${COMPOSE_FILE}" exec -T remote-cloud-relay \
  python -m ros2_trashbot_cloud_relay.remote_cloud_relay \
    --write-cloud-public-ingress-tls-artifact /tmp/trashbot_cloud_public_ingress_tls_missing.json \
    >/tmp/trashbot_cloud_public_ingress_tls_missing_result.json
docker compose -p "${PROJECT_NAME}" -f "${COMPOSE_FILE}" exec -T remote-cloud-relay \
  cat /tmp/trashbot_cloud_public_ingress_tls_missing.json \
    >/tmp/trashbot_cloud_public_ingress_tls_missing.json
cat /tmp/trashbot_cloud_public_ingress_tls_missing.json
echo
python3 - /tmp/trashbot_cloud_public_ingress_tls_missing.json <<'PY'
import json
import sys

payload = json.load(open(sys.argv[1], encoding="utf-8"))
encoded = json.dumps(payload, ensure_ascii=False)
if payload.get("schema") != "trashbot.cloud_public_ingress_tls_gate":
    raise SystemExit("wrong cloud public ingress TLS schema")
if payload.get("evidence_boundary") != "software_proof_docker_cloud_public_ingress_tls_gate":
    raise SystemExit("wrong cloud public ingress TLS evidence boundary")
if payload.get("state") != "missing_public_ingress_tls_config":
    raise SystemExit("missing-config state was not reported")
if payload.get("production_ready") or payload.get("overall_status") != "blocked":
    raise SystemExit("cloud public ingress TLS gate must remain production blocked")
for marker in ("real_https_tls", "public_ingress_external_probe", "dns_resolution", "firewall_public_ingress"):
    if marker not in encoded:
        raise SystemExit(f"missing cloud public ingress TLS marker: {marker}")
for forbidden in ("Authorization", "Bearer", "private key", "certificate path", "/cmd_vel", "ttyUSB", "baudrate", "WAVE ROVER", "http://127.0.0.1"):
    if forbidden in encoded:
        raise SystemExit(f"cloud public ingress TLS leaked forbidden marker: {forbidden}")
PY

echo "== cloud public ingress TLS gate distinguishes config package without external proof =="
docker compose -p "${PROJECT_NAME}" -f "${COMPOSE_FILE}" exec -T \
  -e TRASHBOT_REMOTE_CLOUD_PUBLIC_BASE_URL=https://relay.example.invalid \
  -e TRASHBOT_REMOTE_CLOUD_TLS_MODE=reverse_proxy \
  -e TRASHBOT_REMOTE_CLOUD_PUBLIC_INGRESS=public_https \
  -e TRASHBOT_REMOTE_CLOUD_REVERSE_PROXY_CONFIG=present \
  -e TRASHBOT_REMOTE_CLOUD_FIREWALL_CONFIG=present \
  remote-cloud-relay \
  python -m ros2_trashbot_cloud_relay.remote_cloud_relay \
    --write-cloud-public-ingress-tls-artifact /tmp/trashbot_cloud_public_ingress_tls_present.json \
    >/tmp/trashbot_cloud_public_ingress_tls_present_result.json
docker compose -p "${PROJECT_NAME}" -f "${COMPOSE_FILE}" exec -T remote-cloud-relay \
  cat /tmp/trashbot_cloud_public_ingress_tls_present.json \
    >/tmp/trashbot_cloud_public_ingress_tls_present.json
cat /tmp/trashbot_cloud_public_ingress_tls_present.json
echo
python3 - /tmp/trashbot_cloud_public_ingress_tls_present.json <<'PY'
import json
import sys

payload = json.load(open(sys.argv[1], encoding="utf-8"))
encoded = json.dumps(payload, ensure_ascii=False)
if payload.get("state") != "public_ingress_tls_config_present_not_externally_proven":
    raise SystemExit("config-present-not-proven state was not reported")
if not payload.get("config_package_present"):
    raise SystemExit("config package presence was not reported")
if payload.get("external_probe_proven"):
    raise SystemExit("external proof must remain false")
if payload.get("production_ready") or payload.get("overall_status") != "blocked":
    raise SystemExit("config-present gate must remain production blocked")
for forbidden in ("relay.example.invalid", "Authorization", "Bearer", "private key", "certificate path", "/cmd_vel", "ttyUSB", "baudrate", "WAVE ROVER"):
    if forbidden in encoded:
        raise SystemExit(f"config-present gate leaked forbidden marker: {forbidden}")
PY

echo "== production preflight CLI consumes cloud public ingress TLS gate without production ready =="
set +e
docker compose -p "${PROJECT_NAME}" -f "${COMPOSE_FILE}" exec -T \
  -e TRASHBOT_REMOTE_CLOUD_PUBLIC_INGRESS_TLS_ARTIFACT=/tmp/trashbot_cloud_public_ingress_tls_present.json \
  remote-cloud-relay \
  python -m ros2_trashbot_cloud_relay.remote_cloud_relay --preflight \
  >/tmp/remote_cloud_relay_preflight_public_ingress_tls.json
PREFLIGHT_PUBLIC_INGRESS_TLS_STATUS="$?"
set -e
cat /tmp/remote_cloud_relay_preflight_public_ingress_tls.json
echo
if [ "${PREFLIGHT_PUBLIC_INGRESS_TLS_STATUS}" != "0" ]; then
  echo "public ingress TLS preflight CLI unexpectedly returned ${PREFLIGHT_PUBLIC_INGRESS_TLS_STATUS}" >&2
  exit 1
fi
python3 - /tmp/remote_cloud_relay_preflight_public_ingress_tls.json <<'PY'
import json
import sys

payload = json.load(open(sys.argv[1], encoding="utf-8"))
checks = {check["name"]: check for check in payload.get("checks", [])}
encoded = json.dumps(payload, ensure_ascii=False)
if payload.get("production_ready") or payload.get("overall_status") != "blocked":
    raise SystemExit("public ingress TLS preflight must remain blocked")
if payload.get("evidence_boundary") != "software_proof_docker_cloud_public_ingress_tls_gate":
    raise SystemExit("preflight did not report public ingress TLS boundary")
if checks.get("cloud_public_ingress_tls", {}).get("code") != "public_ingress_tls_config_present_not_externally_proven":
    raise SystemExit("preflight did not preserve config-present-not-proven state")
if checks.get("cloud_public_ingress_tls", {}).get("details", {}).get("external_probe_proven"):
    raise SystemExit("preflight must not claim external proof")
for forbidden in ("relay.example.invalid", "Authorization", "Bearer", "private key", "certificate path", "/cmd_vel", "ttyUSB", "baudrate", "WAVE ROVER"):
    if forbidden in encoded:
        raise SystemExit(f"public ingress TLS preflight leaked forbidden marker: {forbidden}")
PY

echo "== cloud deployment readiness artifact remains blocked-by-design =="
docker compose -p "${PROJECT_NAME}" -f "${COMPOSE_FILE}" exec -T remote-cloud-relay \
  rm -f /tmp/trashbot_cloud_deployment_readiness.json
docker compose -p "${PROJECT_NAME}" -f "${COMPOSE_FILE}" exec -T remote-cloud-relay \
  python -m ros2_trashbot_cloud_relay.remote_cloud_relay \
    --write-cloud-deployment-readiness-artifact /tmp/trashbot_cloud_deployment_readiness.json \
    >/tmp/trashbot_cloud_deployment_readiness.json
cat /tmp/trashbot_cloud_deployment_readiness.json
echo
python3 - /tmp/trashbot_cloud_deployment_readiness.json <<'PY'
import json
import sys

payload = json.load(open(sys.argv[1], encoding="utf-8"))
encoded = json.dumps(payload, ensure_ascii=False)
if not payload.get("ok"):
    raise SystemExit("cloud deployment readiness artifact generation failed")
if payload.get("production_ready"):
    raise SystemExit("cloud deployment readiness must not claim production_ready")
if payload.get("overall_status") != "blocked":
    raise SystemExit("cloud deployment readiness must remain blocked")
if payload.get("evidence_boundary") != "software_proof_docker_cloud_deployment_readiness_gate":
    raise SystemExit("wrong cloud deployment readiness evidence boundary")
for marker in (
    "real_cloud",
    "real_https_tls",
    "real_4g_sim",
    "production_db_or_queue",
    "real_oss_upload",
):
    if marker not in encoded:
        raise SystemExit(f"missing deployment readiness not_proven marker: {marker}")
for forbidden in ("Authorization", "Bearer", "/cmd_vel", "ttyUSB", "baudrate", "WAVE ROVER", "/tmp/remote_cloud"):
    if forbidden in encoded:
        raise SystemExit(f"deployment readiness leaked forbidden marker: {forbidden}")
PY

echo "== cloud external probe bundle covers health ready preflight without production claim =="
docker compose -p "${PROJECT_NAME}" -f "${COMPOSE_FILE}" exec -T remote-cloud-relay \
  rm -f /tmp/trashbot_cloud_external_probe.json
docker compose -p "${PROJECT_NAME}" -f "${COMPOSE_FILE}" exec -T remote-cloud-relay \
  python -m ros2_trashbot_cloud_relay.remote_cloud_relay \
    --write-cloud-external-probe-artifact /tmp/trashbot_cloud_external_probe.json \
    --cloud-external-probe-base-url "http://127.0.0.1:${TRASHBOT_REMOTE_CLOUD_PORT}" \
    >/tmp/trashbot_cloud_external_probe_result.json
docker compose -p "${PROJECT_NAME}" -f "${COMPOSE_FILE}" exec -T remote-cloud-relay \
  cat /tmp/trashbot_cloud_external_probe.json \
    >/tmp/trashbot_cloud_external_probe_artifact.json
cat /tmp/trashbot_cloud_external_probe_artifact.json
echo
python3 - /tmp/trashbot_cloud_external_probe_artifact.json <<'PY'
import json
import sys

payload = json.load(open(sys.argv[1], encoding="utf-8"))
encoded = json.dumps(payload, ensure_ascii=False)
if payload.get("schema") != "trashbot.cloud_external_probe_bundle":
    raise SystemExit("wrong cloud external probe schema")
if payload.get("schema_version") != 1:
    raise SystemExit("wrong cloud external probe schema version")
if payload.get("evidence_boundary") != "software_proof_docker_cloud_external_probe_bundle_gate":
    raise SystemExit("wrong cloud external probe evidence boundary")
if payload.get("production_ready"):
    raise SystemExit("cloud external probe must not claim production_ready")
if payload.get("overall_status") != "blocked":
    raise SystemExit("cloud external probe must remain blocked by production boundary")
endpoints = {item.get("endpoint"): item for item in payload.get("endpoint_results", [])}
if set(endpoints) != {"/healthz", "/readyz", "/preflightz"}:
    raise SystemExit(f"cloud external probe endpoint coverage mismatch: {sorted(endpoints)}")
for endpoint, item in endpoints.items():
    print(f"probe covered {endpoint} http_status={item.get('http_status')} status={item.get('status')}")
    if item.get("status") != "pass":
        raise SystemExit(f"cloud external probe endpoint did not pass: {endpoint}")
if payload.get("redaction_status", {}).get("status") != "pass":
    raise SystemExit("cloud external probe redaction status did not pass")
for marker in ("real_cloud", "real_https_tls", "real_4g_sim", "production_db_or_queue"):
    if marker not in encoded:
        raise SystemExit(f"missing cloud external probe not_proven marker: {marker}")
for forbidden in ("Authorization", "Bearer", "/cmd_vel", "ttyUSB", "baudrate", "WAVE ROVER", "http://127.0.0.1"):
    if forbidden in encoded:
        raise SystemExit(f"cloud external probe leaked forbidden marker: {forbidden}")
PY

echo "== production preflight CLI consumes cloud external probe without production ready =="
set +e
docker compose -p "${PROJECT_NAME}" -f "${COMPOSE_FILE}" exec -T \
  -e TRASHBOT_REMOTE_CLOUD_EXTERNAL_PROBE_ARTIFACT=/tmp/trashbot_cloud_external_probe.json \
  remote-cloud-relay \
  python -m ros2_trashbot_cloud_relay.remote_cloud_relay --preflight \
  >/tmp/remote_cloud_relay_preflight_external_probe.json
PREFLIGHT_EXTERNAL_PROBE_STATUS="$?"
set -e
cat /tmp/remote_cloud_relay_preflight_external_probe.json
echo
if [ "${PREFLIGHT_EXTERNAL_PROBE_STATUS}" != "0" ]; then
  echo "external probe preflight CLI unexpectedly returned ${PREFLIGHT_EXTERNAL_PROBE_STATUS}" >&2
  exit 1
fi
python3 - /tmp/remote_cloud_relay_preflight_external_probe.json <<'PY'
import json
import sys

payload = json.load(open(sys.argv[1], encoding="utf-8"))
checks = {check["name"]: check for check in payload.get("checks", [])}
encoded = json.dumps(payload, ensure_ascii=False)
if payload.get("production_ready"):
    raise SystemExit("external probe preflight must not claim production_ready")
if payload.get("evidence_boundary") != "software_proof_docker_cloud_external_probe_bundle_gate":
    raise SystemExit("preflight did not report cloud external probe boundary")
if checks.get("cloud_external_probe_bundle", {}).get("status") != "pass":
    raise SystemExit("preflight did not recognize cloud external probe artifact")
for endpoint in ("/healthz", "/readyz", "/preflightz"):
    if endpoint not in encoded:
        raise SystemExit(f"preflight external probe missing endpoint: {endpoint}")
for forbidden in ("Authorization", "Bearer", "/cmd_vel", "ttyUSB", "baudrate", "WAVE ROVER", "http://127.0.0.1"):
    if forbidden in encoded:
        raise SystemExit(f"preflight external probe leaked forbidden marker: {forbidden}")
PY

echo "== production preflight CLI with unwritable state expects blocked =="
set +e
repo_ws="$(cd "$relay_root/.." && pwd)"
TRASHBOT_REMOTE_CLOUD_STATE=/dev/null/relay_state.json \
PYTHONPATH="$repo_ws/cloud-relay/src:$repo_ws/onboard/src/ros2_trashbot_behavior" \
python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay --preflight >/tmp/remote_cloud_relay_preflight_cli.json
PREFLIGHT_CLI_STATUS="$?"
set -e
cat /tmp/remote_cloud_relay_preflight_cli.json
echo
if [ "${PREFLIGHT_CLI_STATUS}" != "0" ]; then
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
if payload.get("evidence_boundary") != "software_proof_docker_cloud_db_queue_config_gate":
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

echo "== enqueue pending command for backup restore drill =="
curl -fsS \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"protocol_version":"trashbot.remote.v1","id":"cmd-docker-smoke-restore-pending","type":"confirm_dropoff","expires_at":2778256300.0,"payload":{}}' \
  "${BASE_URL}/robots/trashbot-001/commands"
echo

echo "== sqlite backup restore drill =="
docker compose -p "${PROJECT_NAME}" -f "${COMPOSE_FILE}" exec -T remote-cloud-relay \
  rm -f /tmp/remote_cloud_relay_backup.json /tmp/remote_cloud_relay_restored.sqlite
docker compose -p "${PROJECT_NAME}" -f "${COMPOSE_FILE}" exec -T remote-cloud-relay \
  python -m ros2_trashbot_cloud_relay.remote_cloud_relay \
    --state-backend sqlite \
    --state-path "${TRASHBOT_REMOTE_CLOUD_STATE}" \
    --backup-state-to /tmp/remote_cloud_relay_backup.json \
    --restore-state-path /tmp/remote_cloud_relay_restored.sqlite \
    --backup-restore-drill \
    >/tmp/remote_cloud_relay_backup_restore_drill.json
cat /tmp/remote_cloud_relay_backup_restore_drill.json
echo
python3 - /tmp/remote_cloud_relay_backup_restore_drill.json <<'PY'
import json
import sys

payload = json.load(open(sys.argv[1], encoding="utf-8"))
encoded = json.dumps(payload, ensure_ascii=False)
if not payload.get("ok"):
    raise SystemExit("backup restore drill did not pass")
if payload.get("evidence_boundary") != "software_proof_docker_backup_restore_drill":
    raise SystemExit("wrong backup restore evidence boundary")
checks = payload.get("checks", {})
required_checks = (
    "artifact_checksum",
    "restored_command_http_shape",
    "restored_status_http_shape",
    "restored_ack_http_shape",
    "cursor_ack_conservative",
    "phone_safe_output",
)
for check in required_checks:
    if not checks.get(check):
        raise SystemExit(f"backup restore check failed: {check}")
for marker in (
    "production_backup_policy",
    "real_disaster_recovery",
    "production_db_or_queue",
    "multi_instance_consistency",
):
    if marker not in encoded:
        raise SystemExit(f"missing backup restore boundary marker: {marker}")
for forbidden in ("Authorization", "Bearer", "/cmd_vel", "ttyUSB", "baudrate", "WAVE ROVER", "/tmp/remote_cloud"):
    if forbidden in encoded:
        raise SystemExit(f"backup restore drill leaked forbidden marker: {forbidden}")
PY

echo "== production preflight CLI recognizes local backup artifact without production DR claim =="
set +e
docker compose -p "${PROJECT_NAME}" -f "${COMPOSE_FILE}" exec -T \
  -e TRASHBOT_REMOTE_CLOUD_BACKUP_ARTIFACT=/tmp/remote_cloud_relay_backup.json \
  remote-cloud-relay \
  python -m ros2_trashbot_cloud_relay.remote_cloud_relay --preflight \
  >/tmp/remote_cloud_relay_preflight_backup_drill.json
PREFLIGHT_BACKUP_CLI_STATUS="$?"
set -e
cat /tmp/remote_cloud_relay_preflight_backup_drill.json
echo
if [ "${PREFLIGHT_BACKUP_CLI_STATUS}" != "0" ]; then
  echo "backup drill preflight CLI unexpectedly returned ${PREFLIGHT_BACKUP_CLI_STATUS}" >&2
  exit 1
fi
python3 - /tmp/remote_cloud_relay_preflight_backup_drill.json <<'PY'
import json
import sys

payload = json.load(open(sys.argv[1], encoding="utf-8"))
checks = {check["name"]: check for check in payload.get("checks", [])}
encoded = json.dumps(payload, ensure_ascii=False)
if payload.get("evidence_boundary") != "software_proof_docker_backup_restore_drill":
    raise SystemExit("preflight did not report backup restore drill boundary")
if checks.get("backup_restore_drill", {}).get("status") != "pass":
    raise SystemExit("preflight did not recognize backup restore drill artifact")
for marker in ("production_backup_policy", "real_disaster_recovery", "production_db_or_queue"):
    if marker not in encoded:
        raise SystemExit(f"missing production boundary marker: {marker}")
for forbidden in ("Authorization", "Bearer", "/cmd_vel", "ttyUSB", "baudrate", "WAVE ROVER", "/tmp/remote_cloud"):
    if forbidden in encoded:
        raise SystemExit(f"preflight backup drill leaked forbidden marker: {forbidden}")
PY

echo "== ack pending command after backup restore drill =="
curl -fsS \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"protocol_version":"trashbot.remote.v1","state":"acked","message":"docker smoke pending ack","updated_at":'"${NOW}"',"result":{"bridge":"submitted"}}' \
  "${BASE_URL}/robots/trashbot-001/commands/cmd-docker-smoke-restore-pending/ack"
echo

echo "== restart relay and verify sqlite-backed state recovery =="
docker compose -p "${PROJECT_NAME}" -f "${COMPOSE_FILE}" restart remote-cloud-relay
READY_OK=0
for _ in $(seq 1 20); do
  if curl -fsS "${BASE_URL}/readyz" >/tmp/remote_cloud_relay_readyz_after_restart.json; then
    cat /tmp/remote_cloud_relay_readyz_after_restart.json
    echo
    READY_OK=1
    break
  fi
  sleep 1
done
if [ "${READY_OK}" != "1" ]; then
  echo "readyz did not recover after restart" >&2
  exit 1
fi

curl -fsS \
  -H "Authorization: Bearer ${TOKEN}" \
  "${BASE_URL}/robots/trashbot-001/commands/cmd-docker-smoke-1/ack" \
  >/tmp/remote_cloud_relay_ack_after_restart.json
cat /tmp/remote_cloud_relay_ack_after_restart.json
echo

curl -fsS \
  -H "Authorization: Bearer ${TOKEN}" \
  "${BASE_URL}/robots/trashbot-001/status" \
  >/tmp/remote_cloud_relay_status_after_restart.json
cat /tmp/remote_cloud_relay_status_after_restart.json
echo

curl -fsS \
  -H "Authorization: Bearer ${TOKEN}" \
  "${BASE_URL}/robots/trashbot-001/commands/next?last_ack_id=cmd-docker-smoke-1" \
  >/tmp/remote_cloud_relay_next_after_restart.json
cat /tmp/remote_cloud_relay_next_after_restart.json
echo

python3 - /tmp/remote_cloud_relay_ack_after_restart.json /tmp/remote_cloud_relay_status_after_restart.json /tmp/remote_cloud_relay_next_after_restart.json <<'PY'
import json
import sys

ack = json.load(open(sys.argv[1], encoding="utf-8"))
status = json.load(open(sys.argv[2], encoding="utf-8"))
next_command = json.load(open(sys.argv[3], encoding="utf-8"))
if ack.get("ack", {}).get("state") != "acked":
    raise SystemExit("ack was not recovered after restart")
if status.get("status", {}).get("state") != "idle":
    raise SystemExit("status was not recovered after restart")
if next_command.get("command") is not None:
    raise SystemExit("terminal ack cursor semantics changed after restart")
PY
