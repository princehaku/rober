# Tech Done - Mac Docker Humble Env

## Robot Platform Engineer

### Actual changes

- `docker-compose.humble.yml`
  - Removed the default `/tmp/.X11-unix` bind mount from the `humble` service so Mac Docker Desktop/Engine runs do not depend on a Linux X11 socket path.
  - Added `ROS_HUMBLE_BASE_IMAGE` to Compose build args to match the build script override surface.
  - Added an explicit `x11` profile service, `humble-x11`, for Linux/X11 GUI runs that intentionally need `DISPLAY`, `QT_X11_NO_MITSHM`, and `/tmp/.X11-unix`.
- `scripts/docker_humble_dev.sh`
  - Changed the entry comment and defaults from WSL/Linux-first to macOS/Linux.
  - Made X11 environment and `/tmp/.X11-unix` mounting opt-in through `ROS_HUMBLE_ENABLE_X11=1`.
  - If X11 is enabled but `/tmp/.X11-unix` is absent, the script prints a warning and continues without manufacturing a host bind path.
- `scripts/docker_humble_build.sh`
  - Extended `classify_build_failure` to recognize BuildKit content-store integrity failures from base image fetches, including `failed size validation`, `failed precondition`, and `unknown-sha256`.
  - Classifies this path as `registry mirror/cache`, with operator next steps to remove or change Docker Desktop registry mirrors/proxy, restart Docker Desktop, clear builder cache, verify `docker pull osrf/ros:humble-desktop`, or use a trusted exported image tar through `ROS_HUMBLE_IMAGE_TAR` plus `SKIP_DOCKER_BUILD=1`.
- `README.md`
  - Rewrote the Docker Humble section from WSL-first to Mac-first.
  - Documented that Mac runs should start from a local path such as `/Users/<user>/apps/rober`, not `/mnt/e/...` WSL paths.
  - Kept Linux/WSL mirror setup as an optional non-default path.
  - Documented default Compose usage without X11 and explicit Linux/X11 opt-in commands.

### Validation

Passed:

```bash
bash -n scripts/docker_humble_dev.sh
exit=0
```

```bash
docker compose -f docker-compose.humble.yml config
exit=0
# Relevant output:
# services.humble.volumes:
#   - /Users/m4/apps/rober:/ws
#   - /Users/m4/apps/rober/.ros_home:/root/.ros
# No /tmp/.X11-unix mount appears in the default humble service.
```

```bash
ROS_HUMBLE_ENABLE_X11=1 docker compose -f docker-compose.humble.yml --profile x11 config
exit=0
# Relevant output:
# services.humble-x11.profiles:
#   - x11
# services.humble-x11.environment.ROS_HUMBLE_ENABLE_X11: "1"
# services.humble-x11.volumes includes:
#   - /tmp/.X11-unix:/tmp/.X11-unix
```

```bash
git diff --check -- docker-compose.humble.yml scripts/docker_humble_dev.sh README.md sprints/2026.05.12_01-02_mac-docker-humble-env/tech-done.md
exit=0
```

```bash
bash -n scripts/docker_humble_build.sh
exit=0
```

```bash
git diff --check -- scripts/docker_humble_build.sh sprints/2026.05.12_01-02_mac-docker-humble-env/tech-done.md
exit=0
```

### Failure classification

- Earlier fenced validation had no Compose config failure. Docker daemon reachability was sufficient for `docker compose config`; no build or container start was requested in that validation.
- User-provided Mac rerun of `docker compose -f docker-compose.humble.yml build --pull --no-cache humble` still blocks while loading metadata for `docker.io/osrf/ros:humble-desktop` with `failed commit on ref unknown-sha256:... failed size validation: 1383 != 1224: failed precondition`.
- Current classification: `registry mirror/cache`. The failure occurs before repository Dockerfile steps and before ROS2 workspace build, so it is treated as Docker Desktop registry mirror/proxy or BuildKit content-store/cache integrity failure, not a ROS package failure.

### Remaining risk

- Mac-first Compose rendering has passed `docker compose config`, but full Docker build remains blocked at base image pull/metadata integrity validation for `osrf/ros:humble-desktop`.
- Operator still needs to remove or change Docker Desktop registry mirrors/proxy, restart Docker Desktop, clear builder cache, retry pulling the base image, or load a trusted tar before this host can prove the Docker/Humble build path.
- This change validates shell syntax and failure classification only. It does not prove that a full Docker build or ROS2 workspace build succeeds on the current Mac host.
- X11 GUI support remains a Linux/XQuartz operator path and may require host-specific DISPLAY/XQuartz setup outside this repository.
- `scripts/docker_humble_dev.sh` still uses `--network host`, which Docker Desktop on macOS handles differently from native Linux; this sprint only removed stale WSL/Linux X11 path defaults and did not validate ROS network behavior inside a running container.

## Robot Platform Engineer Re-Validation - Docker Desktop Fixed

### Actual changes

- `sprints/2026.05.12_01-02_mac-docker-humble-env/tech-done.md`
  - Added the 2026-05-12 Mac local Docker/Humble re-validation result after the user reported Docker Desktop was fixed.
  - Updated the status boundary from `registry mirror/cache blocked` to `Docker/Humble entry restored; ROS2 workspace packaging now blocks full colcon`.

### Validation

Passed:

```bash
docker pull osrf/ros:humble-desktop
# Digest: sha256:49e87123022a2622a8a098eb3d71d6df8265469ad4d46c6dbde0326f8aa97bb3
# Status: Downloaded newer image for osrf/ros:humble-desktop
# docker.io/osrf/ros:humble-desktop
```

```bash
docker compose -f docker-compose.humble.yml build --pull --no-cache humble
# [internal] load metadata for docker.io/osrf/ros:humble-desktop ... DONE
# FROM docker.io/osrf/ros:humble-desktop@sha256:49e87123022a2622a8a098eb3d71d6df8265469ad4d46c6dbde0326f8aa97bb3 ... DONE
# apt-get update ... Fetched 47.7 MB
# rosdep update --rosdistro humble ... Add distro "humble"
# naming to docker.io/library/ros-rbs-humble:dev done
# ros-rbs-humble:dev  Built
```

Failed after entering the next stage:

```bash
docker compose -f docker-compose.humble.yml run --rm humble bash -lc "unset AMENT_PREFIX_PATH CMAKE_PREFIX_PATH COLCON_PREFIX_PATH && source /opt/ros/humble/setup.bash && rm -rf build install log && colcon build --symlink-install"
# Starting >>> ros2_trashbot_interfaces
# Starting >>> ros2_trashbot_vision
# Finished <<< ros2_trashbot_vision [1.03s]
# Finished <<< ros2_trashbot_interfaces [25.8s]
# Starting >>> ros2_trashbot_nav
# Starting >>> ros2_trashbot_hardware
# Finished <<< ros2_trashbot_nav [1.20s]
# Starting >>> ros2_trashbot_behavior
# Finished <<< ros2_trashbot_hardware [1.26s]
# Finished <<< ros2_trashbot_behavior [1.02s]
# Starting >>> ros2_trashbot_bringup
# CMake Error at ament_cmake_symlink_install/ament_cmake_symlink_install.cmake:105 (message):
#   ament_cmake_symlink_install_directory() can't find
#   '/ws/src/ros2_trashbot_bringup/config'
# Summary: 5 packages finished [31.5s]
#   1 package failed: ros2_trashbot_bringup
```

Not run:

```bash
docker compose -f docker-compose.humble.yml run --rm humble bash -lc "source /opt/ros/humble/setup.bash && source /ws/install/setup.bash && ros2 pkg prefix ros2_trashbot_bringup"
```

Reason: the required preceding `colcon build --symlink-install` step failed before a valid `ros2_trashbot_bringup` install could be proven.

Failure locator commands required by the sprint:

```bash
docker info --format 'ServerVersion={{.ServerVersion}} RegistryMirrors={{json .RegistryConfig.Mirrors}}'
# ServerVersion=28.3.3 RegistryMirrors=null
```

```bash
docker buildx ls
# NAME/NODE           DRIVER/ENDPOINT     STATUS    BUILDKIT   PLATFORMS
# desktop-linux*      docker
#  \_ desktop-linux    \_ desktop-linux   running   v0.23.2    linux/amd64 (+2), linux/arm64, linux/ppc64le, linux/s390x, (2 more)
# default                                 error
# Cannot load builder default: Cannot connect to the Docker daemon at unix:///var/run/docker.sock. Is the docker daemon running?
```

Additional read-only root-cause check:

```bash
find src/ros2_trashbot_bringup -maxdepth 3 -type d -print
# src/ros2_trashbot_bringup
# src/ros2_trashbot_bringup/test
# src/ros2_trashbot_bringup/launch
```

```cmake
install(DIRECTORY launch config
  DESTINATION share/${PROJECT_NAME})
```

### Failure classification

- Previous blocker `registry mirror/cache` is cleared for this host: direct `docker pull osrf/ros:humble-desktop` passed, and `docker compose ... build --pull --no-cache humble` built `ros-rbs-humble:dev` successfully.
- Current blocker is `ROS2 workspace packaging/config`: `src/ros2_trashbot_bringup/CMakeLists.txt` installs both `launch` and `config`, but the package currently has no `src/ros2_trashbot_bringup/config` directory. `ament_cmake_symlink_install_directory()` fails at install time.
- Docker builder state is acceptable for this path: `desktop-linux` is running with BuildKit v0.23.2 and Compose successfully used it. The stale `default` builder entry still reports a daemon socket error, but it did not block the required Compose build.

### Remaining risk

- This sprint now proves Docker Desktop registry/cache recovery through base image pull and no-cache Compose image build on the Mac host.
- Full ROS2 workspace build is still blocked by the missing bringup `config` install source. Fixing that requires a follow-up Robot Platform Engineer change in `src/ros2_trashbot_bringup`, which is outside this task's allowed file scope.
- `ros2 pkg prefix ros2_trashbot_bringup` is not proven because the workspace build did not complete.
- No HIL, serial device, WAVE ROVER, `/dev/ttyUSB0`, `/cmd_vel`, `/odom`, `/imu/data`, or `/battery` evidence was produced or claimed in this validation.

## Robot Platform Engineer Packaging Fix - Bringup Install Contract

### Actual changes

- `src/ros2_trashbot_bringup/CMakeLists.txt`
  - Removed the stale `config` directory from the bringup package install contract.
  - Kept installation scoped to the existing `launch` directory because this package currently has no local default config directory.
- `sprints/2026.05.12_01-02_mac-docker-humble-env/tech-done.md`
  - Added this packaging fix, Docker/Humble workspace build result, package prefix proof, and non-HIL risk boundary.

### Validation

Passed:

```bash
docker compose -f docker-compose.humble.yml run --rm humble bash -lc "unset AMENT_PREFIX_PATH CMAKE_PREFIX_PATH COLCON_PREFIX_PATH && source /opt/ros/humble/setup.bash && rm -rf build install log && colcon build --symlink-install"
# Starting >>> ros2_trashbot_interfaces
# Starting >>> ros2_trashbot_vision
# Finished <<< ros2_trashbot_vision [0.97s]
# Finished <<< ros2_trashbot_interfaces [26.2s]
# Starting >>> ros2_trashbot_nav
# Starting >>> ros2_trashbot_hardware
# Finished <<< ros2_trashbot_hardware [1.25s]
# Finished <<< ros2_trashbot_nav [1.33s]
# Starting >>> ros2_trashbot_behavior
# Finished <<< ros2_trashbot_behavior [1.03s]
# Starting >>> ros2_trashbot_bringup
# Finished <<< ros2_trashbot_bringup [3.49s]
# Summary: 6 packages finished [32.4s]
```

Note: the container shell printed `not found: "/ws/install/ros2_trashbot_bringup/share/ros2_trashbot_bringup/local_setup.bash"` before the build started because its entry shell tried to source an old install prefix. The commanded build then unset prefix variables, removed `build install log`, and completed successfully.

```bash
docker compose -f docker-compose.humble.yml run --rm humble bash -lc "source /opt/ros/humble/setup.bash && source /ws/install/setup.bash && ros2 pkg prefix ros2_trashbot_bringup"
# /ws/install/ros2_trashbot_bringup
```

### Failure classification

- Root cause was `ROS2 workspace packaging/config`: `src/ros2_trashbot_bringup/CMakeLists.txt` installed `launch config`, but `src/ros2_trashbot_bringup/config` did not exist.
- No local bringup config files were required by the package after checking the launch sources; existing `config` usage points to `ros2_trashbot_nav/config/nav2_params.yaml`, not to a bringup-owned directory.

### Remaining risk

- This is Docker/Humble software packaging proof only.
- No HIL, serial device, WAVE ROVER, `/dev/ttyUSB0`, `/cmd_vel`, `/odom`, `/imu/data`, `/battery`, or physical motion evidence was produced or claimed.
