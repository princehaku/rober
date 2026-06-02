#!/usr/bin/env bash
set -euo pipefail

# O7 持久化入口只安装 8088 camera smoke，不触碰 ROS2、串口、WAVE ROVER 或 cmd_vel。
UNIT_NAME="trashbot-local-webrtc-camera.service"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
REPO_ROOT="${ROBER_REPO_ROOT:-${DEFAULT_REPO_ROOT}}"
SYSTEMD_DIR="${SYSTEMD_DIR:-/etc/systemd/system}"
DRY_RUN=0
ENABLE_UNIT=1
START_UNIT=1

usage() {
  cat <<'EOF'
Usage: install_o7_camera_service.sh [--dry-run] [--repo-root PATH] [--systemd-dir PATH] [--no-enable] [--no-start]

Installs trashbot-local-webrtc-camera.service for the LAN-only O7 camera smoke.
Defaults: HOST=0.0.0.0 PORT=8088 ROBER_CAMERA_SOURCE=auto.
Safety: no serial open, no WAVE ROVER JSON, no ROS2 launch, no /cmd_vel.
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
SMOKE_SCRIPT="${REPO_ROOT}/onboard/scripts/local_webrtc_camera_smoke.sh"
UNIT_PATH="${SYSTEMD_DIR}/${UNIT_NAME}"

require_file() {
  local path="$1"
  [[ -f "$path" ]] || { echo "error: required file missing: $path" >&2; exit 1; }
}

print_step() {
  printf '%s\n' "$*"
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
  # repo root 可能包含 / 或 &；替换 unit 模板时必须转义，避免生成坏 ExecStart。
  printf '%s' "$1" | sed -e 's/[\/&]/\\&/g'
}

require_file "${TEMPLATE_PATH}"
require_file "${SMOKE_SCRIPT}"

if [[ "${DRY_RUN}" -eq 0 ]]; then
  command -v systemctl >/dev/null 2>&1 || { echo "error: systemctl not found; cannot install systemd unit" >&2; exit 1; }
  [[ -d "${SYSTEMD_DIR}" ]] || { echo "error: systemd dir missing: ${SYSTEMD_DIR}" >&2; exit 1; }
fi

print_step "unit_name=${UNIT_NAME}"
print_step "repo_root=${REPO_ROOT}"
print_step "systemd_dir=${SYSTEMD_DIR}"
print_step "defaults=HOST=0.0.0.0 PORT=8088 ROBER_CAMERA_SOURCE=auto"
print_step "safety=no_serial_no_wave_rover_json_no_ros2_no_cmd_vel"

if [[ "${DRY_RUN}" -eq 1 ]]; then
  print_step "[dry-run] render ${TEMPLATE_PATH} -> ${UNIT_PATH} with @ROBER_REPO_ROOT@=${REPO_ROOT}"
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
  # restart 只影响 camera smoke HTTP 服务；不会发 /offer，也不会触发机器人运动。
  run_or_echo systemctl restart "${UNIT_NAME}"
  run_or_echo systemctl --no-pager --full status "${UNIT_NAME}"
else
  print_step "start_skipped=true"
fi
