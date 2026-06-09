#!/usr/bin/env bash
set +e

RUN_ID="map_lifecycle_proof_refresh_$(date +%Y%m%d_%H%M%S)"
RUN_DIR="${1:-/tmp/${RUN_ID}}"
API="http://127.0.0.1:8787"

mkdir -p "${RUN_DIR}/runtime_maps" "${RUN_DIR}/runtime_logs"

run_cmd() {
  local name="$1"
  shift
  {
    echo "### ${name}"
    echo "### command: $*"
    echo "### started_at: $(date -Is)"
    "$@"
    local code=$?
    echo "### exit_code: ${code}"
    echo "### finished_at: $(date -Is)"
  } >"${RUN_DIR}/${name}.txt" 2>&1
  return 0
}

curl_capture() {
  local name="$1"
  local method="$2"
  local path="$3"
  local body="${4:-}"
  if [ "${method}" = "POST" ]; then
    curl -sS --max-time 180 -w '\nHTTP_STATUS:%{http_code}\n' \
      -X POST "${API}${path}" \
      -H "Content-Type: application/json" \
      -d "${body}" >"${RUN_DIR}/${name}.json" 2>"${RUN_DIR}/${name}.stderr" || true
  else
    curl -sS --max-time 60 -w '\nHTTP_STATUS:%{http_code}\n' \
      "${API}${path}" >"${RUN_DIR}/${name}.json" 2>"${RUN_DIR}/${name}.stderr" || true
  fi
  return 0
}

ros_cmd() {
  local name="$1"
  shift
  {
    echo "### ${name}"
    echo "### started_at: $(date -Is)"
    source /opt/ros/humble/setup.bash
    for setup in /root/rober/onboard/install/setup.bash /ws/install/setup.bash; do
      [ -f "${setup}" ] && source "${setup}"
    done
    "$@"
    local code=$?
    echo "### exit_code: ${code}"
    echo "### finished_at: $(date -Is)"
  } >"${RUN_DIR}/${name}.txt" 2>&1
  return 0
}

run_cmd pre_hostname_date hostname
run_cmd pre_date date -Is
run_cmd pre_service_status systemctl status trashbot-upper-robot-api.service --no-pager
run_cmd pre_upper_api_process pgrep -af "upper_robot_api.py"
run_cmd pre_device_enum bash -lc 'ls -l /dev/ttyS5 /dev/ttyACM0 /dev/serial/by-id /dev/serial/by-path 2>&1 || true; readlink -f /dev/ttyS5 /dev/ttyACM0 2>&1 || true'
run_cmd pre_lsof_ttyS5_ttyACM0 bash -lc 'lsof /dev/ttyS5 /dev/ttyACM0 2>&1 || true'
ros_cmd pre_ros_topic_list ros2 topic list -t
run_cmd pre_map_runtime_listing bash -lc 'for d in /root/rober/onboard/runtime /root/rober/onboard/runtime/maps /root/rober/runtime; do echo "## $d"; find "$d" -maxdepth 3 -type f -o -type d 2>&1 | sort || true; done'
curl_capture pre_api_map_proof_latest_response GET /api/map/proof/latest
curl_capture pre_api_map_list_response GET /api/map/list

curl_capture api_map_proof_refresh_response POST /api/map/proof/refresh '{"timeout_s":60}'

curl_capture post_api_map_proof_latest_response GET /api/map/proof/latest
curl_capture post_api_map_list_response GET /api/map/list
curl_capture post_api_nav2_status_response GET /api/nav2/status
ros_cmd post_ros_topic_list ros2 topic list -t
run_cmd post_lsof_ttyS5_ttyACM0 bash -lc 'lsof /dev/ttyS5 /dev/ttyACM0 2>&1 || true'
run_cmd post_map_runtime_listing bash -lc 'for d in /root/rober/onboard/runtime /root/rober/onboard/runtime/maps /root/rober/runtime; do echo "## $d"; find "$d" -maxdepth 4 -type f -o -type d 2>&1 | sort || true; done'
run_cmd post_map_runtime_processes bash -lc 'pgrep -af "o3_map_lifecycle_proof|slam_toolbox|map_saver|map_lifecycle|lidar_driver|ros2 launch" || true'

for path in \
  /root/rober/onboard/runtime/map_lifecycle_latest.json \
  /root/rober/runtime/map_lifecycle_latest.json
do
  if [ -f "${path}" ]; then
    cp -a "${path}" "${RUN_DIR}/$(basename "$(dirname "${path}")")_$(basename "${path}")" || true
  fi
done

if [ -d /root/rober/onboard/runtime/maps ]; then
  cp -a /root/rober/onboard/runtime/maps/. "${RUN_DIR}/runtime_maps/" || true
fi

for path in /tmp/rober_map_lifecycle_proof_runtime_*.log /tmp/o3_map_lifecycle_proof*.log; do
  [ -f "${path}" ] && cp -a "${path}" "${RUN_DIR}/runtime_logs/" || true
done

run_cmd final_lsof_and_runtime_processes bash -lc 'echo "## lsof"; lsof /dev/ttyS5 /dev/ttyACM0 2>&1 || true; echo "## processes"; pgrep -af "o3_map_lifecycle_proof|slam_toolbox|map_saver|map_lifecycle|lidar_driver|ros2 launch" || true'
ros_cmd final_ros_topic_list ros2 topic list -t

echo "${RUN_DIR}" >"${RUN_DIR}/RUN_DIR.txt"
find "${RUN_DIR}" -maxdepth 4 -type f | sort >"${RUN_DIR}/FILES.txt"
cat "${RUN_DIR}/RUN_DIR.txt"
