#!/usr/bin/env bash
set -euo pipefail

# 安装 8787 统一上位机 API；不会安装云中转，也不会改 ROS2 launch。
UNIT_NAME="trashbot-upper-robot-api.service"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
REPO_ROOT="${ROBER_REPO_ROOT:-${DEFAULT_REPO_ROOT}}"
SYSTEMD_DIR="${SYSTEMD_DIR:-/etc/systemd/system}"
DRY_RUN=0
ENABLE_UNIT=1
START_UNIT=1

usage() {
  cat <<'EOF'
Usage: install_upper_robot_api_service.sh [--dry-run] [--repo-root PATH] [--systemd-dir PATH] [--no-enable] [--no-start]

Installs trashbot-upper-robot-api.service for the unified Orange Pi robot API.
Defaults: HOST=0.0.0.0 PORT=8787 CAMERA=http://127.0.0.1:8088 BASE=/dev/ttyS5.
Safety: base manual commands are low-speed pulses with automatic T=1 L=0 R=0 stop.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --repo-root)
      [[ $# -ge 2 ]] || { echo "error: --repo-root requires PATH" >&2; exit 2; }
      REPO_ROOT="$2"
      shift 2
      ;;
    --systemd-dir)
      [[ $# -ge 2 ]] || { echo "error: --systemd-dir requires PATH" >&2; exit 2; }
      SYSTEMD_DIR="$2"
      shift 2
      ;;
    --no-enable)
      ENABLE_UNIT=0
      shift
      ;;
    --no-start)
      START_UNIT=0
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "error: unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

TEMPLATE_PATH="${REPO_ROOT}/onboard/systemd/${UNIT_NAME}"
API_SCRIPT="${REPO_ROOT}/onboard/scripts/upper_robot_api.sh"
LOCAL_TEMPLATE_PATH="${DEFAULT_REPO_ROOT}/onboard/systemd/${UNIT_NAME}"
LOCAL_API_SCRIPT="${DEFAULT_REPO_ROOT}/onboard/scripts/upper_robot_api.sh"
UNIT_PATH="${SYSTEMD_DIR}/${UNIT_NAME}"

require_file() {
  local path="$1"
  [[ -f "$path" ]] || { echo "error: required file missing: $path" >&2; exit 1; }
}

run_or_echo() {
  if [[ "${DRY_RUN}" -eq 1 ]]; then
    printf '[dry-run]'
    printf ' %q' "$@"
    printf '\n'
  else
    "$@"
  fi
}

escape_sed_replacement() {
  # repo root 可能包含 / 或 &；渲染 unit 时必须转义。
  printf '%s' "$1" | sed -e 's/[\/&]/\\&/g'
}

if [[ "${DRY_RUN}" -eq 1 ]]; then
  # dry-run 常用于在本机预演远端 /root/rober 路径，源文件用当前仓库校验即可。
  require_file "${LOCAL_TEMPLATE_PATH}"
  require_file "${LOCAL_API_SCRIPT}"
else
  require_file "${TEMPLATE_PATH}"
  require_file "${API_SCRIPT}"
fi

if [[ "${DRY_RUN}" -eq 0 ]]; then
  command -v systemctl >/dev/null 2>&1 || { echo "error: systemctl not found" >&2; exit 1; }
  [[ -d "${SYSTEMD_DIR}" ]] || { echo "error: systemd dir missing: ${SYSTEMD_DIR}" >&2; exit 1; }
fi

printf 'unit_name=%s\n' "${UNIT_NAME}"
printf 'repo_root=%s\n' "${REPO_ROOT}"
printf 'systemd_dir=%s\n' "${SYSTEMD_DIR}"
printf 'defaults=HOST=0.0.0.0 PORT=8787 CAMERA=http://127.0.0.1:8088 BASE=/dev/ttyS5\n'
printf 'safety=low_speed_pulse_auto_stop_no_cloud_relay\n'

if [[ "${DRY_RUN}" -eq 1 ]]; then
  printf '[dry-run] render %s -> %s with @ROBER_REPO_ROOT@=%s\n' "${TEMPLATE_PATH}" "${UNIT_PATH}" "${REPO_ROOT}"
else
  tmp_unit="$(mktemp)"
  trap 'rm -f "${tmp_unit:-}"' EXIT
  sed "s/@ROBER_REPO_ROOT@/$(escape_sed_replacement "${REPO_ROOT}")/g" "${TEMPLATE_PATH}" > "${tmp_unit}"
  install -m 0644 "${tmp_unit}" "${UNIT_PATH}"
fi

run_or_echo systemctl daemon-reload

if [[ "${ENABLE_UNIT}" -eq 1 ]]; then
  run_or_echo systemctl enable "${UNIT_NAME}"
fi

if [[ "${START_UNIT}" -eq 1 ]]; then
  run_or_echo systemctl restart "${UNIT_NAME}"
  run_or_echo systemctl --no-pager --full status "${UNIT_NAME}"
else
  printf 'start_skipped=true\n'
fi
