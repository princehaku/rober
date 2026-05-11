# Sprint 2026.05.12_00-02 O1 Docker Image Tar Reuse - Tech Done

## 状态

- 阶段：tech-done
- 时间：2026-05-12 00:30 Asia/Shanghai
- Engineering Owner：`robot-software-engineer`
- 证据范围：`software_proof_docker_only`

## 实际改动

- `scripts/docker_humble_build.sh`
  - 新增 `ROS_HUMBLE_IMAGE_TAR` 入口，默认未设置时保持原有 build / skip-build 行为。
  - 当 `ROS_HUMBLE_IMAGE_TAR` 被设置为空时快速失败，输出 `image_tar_state=empty_error` 和 `evidence_scope=software_proof_docker_only`，不进入 Docker build。
  - 当 `ROS_HUMBLE_IMAGE_TAR` 指向不存在文件时快速失败，输出 `image_tar_state=missing_error` 和 tar 路径，且不进入 Docker build。
  - 当 `ROS_HUMBLE_IMAGE_TAR` 被设置但 `SKIP_DOCKER_BUILD` 不是 `1` 时快速失败；本轮采用“tar reuse 只能和 `SKIP_DOCKER_BUILD=1` 同用”的策略，避免 load 后继续 build 的语义混乱。
  - 当 `ROS_HUMBLE_IMAGE_TAR` 指向普通文件且 `SKIP_DOCKER_BUILD=1` 时，脚本会先执行 `docker load -i "$ROS_HUMBLE_IMAGE_TAR"`，再沿用现有 `target_image_present` 与 `validate_target_image_for_reuse` 校验。`docker load` 成功不等于通过。
  - Docker/Humble preflight 新增 `image_tar_state=unset|provided|empty_error|missing_error`，提供 tar 路径用于 operator 复盘。
  - operator 提示补充：tar 必须来自可信机器导出的可运行目标镜像，tar 内 tag 必须匹配 `ROS_HUMBLE_IMAGE`，Docker daemon 需要可用，也可取消 skip build 并修复 registry mirror/proxy 后重建。

## 验证结果

```bash
bash -n scripts/docker_humble_build.sh
```

结果：exit 0，无输出。

```bash
ROS_HUMBLE_IMAGE_TAR= SKIP_DOCKER_BUILD=1 bash scripts/docker_humble_build.sh
```

结果：exit 2，符合预期；关键输出：

```text
ERROR: ROS_HUMBLE_IMAGE_TAR is set but empty. Provide a Docker image tar path, or unset it.
evidence_scope=software_proof_docker_only
target_image=ros-rbs-humble:dev
skip_docker_build=1
image_tar_state=empty_error
```

```bash
ROS_HUMBLE_IMAGE_TAR=/tmp/does-not-exist.tar SKIP_DOCKER_BUILD=1 bash scripts/docker_humble_build.sh
```

结果：exit 2，符合预期；关键输出：

```text
ERROR: ROS_HUMBLE_IMAGE_TAR does not point to an existing file: /tmp/does-not-exist.tar
evidence_scope=software_proof_docker_only
target_image=ros-rbs-humble:dev
skip_docker_build=1
image_tar_state=missing_error
image_tar_path=/tmp/does-not-exist.tar
```

```bash
SKIP_DOCKER_BUILD=1 bash scripts/docker_humble_build.sh
```

结果：exit 4，符合 blocked evidence；本机目标镜像 tag 存在但不可运行。关键输出：

```text
image_tar_state=unset
local_target_image_present=yes
local_image_reuse=inspect_present_validation_pending
docker: Error response from daemon: error walking manifest for docker.io/library/ros-rbs-humble:dev: descriptor is neither a manifest or index
ERROR: SKIP_DOCKER_BUILD=1 found target image 'ros-rbs-humble:dev', but it is not runnable as a ROS Humble build image.
evidence_scope=software_proof_docker_only
```

补充围栏：

```bash
ROS_HUMBLE_IMAGE_TAR=/etc/hosts bash scripts/docker_humble_build.sh
```

结果：exit 2；tar 已提供但未设置 `SKIP_DOCKER_BUILD=1` 时快速失败，不进入 Docker build。

## 失败定位

- 脚本语法与 tar 参数围栏通过。
- `SKIP_DOCKER_BUILD=1` 仍被本机已有不可运行 `ros-rbs-humble:dev` tag 阻塞，失败点是 Docker daemon 在 `docker run` 探针阶段返回 `descriptor is neither a manifest or index`。这不是本轮脚本逻辑失败，而是上一轮已记录的本地目标镜像不可运行状态。

## 剩余风险

- 本轮没有真实 `ros-rbs-humble:dev` tar，因此未覆盖成功 `docker load` 后的完整 colcon build。
- tar 内部 tag 如果不匹配 `ROS_HUMBLE_IMAGE`，脚本会在 load 后继续通过目标镜像 inspect / runnable probe 拦截，但 operator 仍需用可信导出源控制 tar 内容。
- 本轮仍为 `software_proof_docker_only`，不包含 WAVE ROVER、ESP32、Orange Pi、UART 或真实 HIL evidence packet，不得声明 `hil_pass`。

## 协同需求

- Product：当前无范围决策需求；本轮不更新 `OKR.md`。
- Hardware：暂不需要；没有触碰硬件、串口、引脚、电压、底盘协议或 vendor 文件。
- Autonomy：暂不需要；没有触碰 Nav2、SLAM、巡逻或 route replay。
- Full-Stack：暂不需要；没有触碰 Web/API/UI。
