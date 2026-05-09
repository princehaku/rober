#!/usr/bin/env bash
# WSL/Linux bash helper. Uses python3 to match ROS2 project syntax (type hints in source).
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

missing_test_packages=()

source_paths=(
    "$repo_root/src/ros2_trashbot_interfaces"
    "$repo_root/src/ros2_trashbot_hardware"
    "$repo_root/src/ros2_trashbot_nav"
    "$repo_root/src/ros2_trashbot_bringup"
    "$repo_root/src/ros2_trashbot_behavior"
    "$repo_root/src/ros2_trashbot_vision"
)

previous_pythonpath="${PYTHONPATH:-}"
pythonpath_join="$(printf '%s:' "${source_paths[@]}")"
pythonpath_join="${pythonpath_join%:}"
if [ -n "$previous_pythonpath" ]; then
  export PYTHONPATH="$pythonpath_join:$previous_pythonpath"
else
  export PYTHONPATH="$pythonpath_join"
fi

python3 -m compileall -q src scripts

package_tests=(
  "ros2_trashbot_interfaces src/ros2_trashbot_interfaces"
  "ros2_trashbot_hardware src/ros2_trashbot_hardware"
  "ros2_trashbot_nav src/ros2_trashbot_nav"
  "ros2_trashbot_bringup src/ros2_trashbot_bringup"
  "ros2_trashbot_behavior src/ros2_trashbot_behavior"
  "ros2_trashbot_vision src/ros2_trashbot_vision"
)

for item in "${package_tests[@]}"; do
  set -- $item
  name="$1"
  package_path="$2"
  full_path="$repo_root/$package_path"
  test_path="$full_path/test"

  if [ ! -d "$test_path" ]; then
    echo "No python test folder for package $name (expected $test_path)"
    missing_test_packages+=("$name")
    continue
  fi

  python3 -m unittest discover -s "$test_path" -p "test*.py"
done

if [ ${#missing_test_packages[@]} -gt 0 ]; then
  echo "Smoke scan skipped test execution for: ${missing_test_packages[*]}"
fi

if [ "${ROBOT_DAILY_DOCKER_BUILD:-}" = "1" ]; then
  echo "ROBOT_DAILY_DOCKER_BUILD=1, running Docker Humble build validation."
  "$repo_root/scripts/docker_humble_build.sh"
fi
