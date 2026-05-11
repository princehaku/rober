# Sprint 2026.05.11_21-22 O1 Docker Humble Preflight Unblock - Tech Done

## 状态

- 阶段：tech-done
- 时间：2026-05-11 21:14 Asia/Shanghai
- Owner：`hardware-engineer`
- 结论：Docker/Humble preflight 仍 blocked，但已可精确归因为 `registry mirror/proxy` 返回 HTML；HIL 仍因本机无真实串口设备保持 blocked，不声明 `hil_pass`。

## 已读 vendor 来源

- `AGENTS.md`
- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`

## 已证实硬件结论

- Vendor WAVE ROVER 上位机参考使用 UART 串口、UTF-8 JSON、每行一个 JSON 对象并以 `\n` 结束。
- Vendor Raspberry Pi 参考默认使用 `/dev/ttyAMA0`、`115200`；本项目 Orange Pi/WAVE ROVER 上车前仍必须现场确认实际串口路径。
- `T=143` 关闭 echo、`T=142` 设置反馈间隔、`T=131` 开启底盘反馈流；`T=1001` 是底盘反馈帧。
- 当前本机无 `/dev/ttyUSB*`、`/dev/ttyAMA*`、`/dev/serial*` 候选，`python3 scripts/hardware_smoke_wave_rover.py --status` 只能作为 `source=software_proof` readiness/blocked evidence。

## 实际改动

- `scripts/docker_humble_build.sh`
  - 构建前输出 Docker daemon/context/builder/base image/registry mirror/proxy 状态。
  - 捕获 `docker build` 日志并在失败时输出 `Docker build failure classification`。
  - 分类覆盖 `Docker daemon`、`Docker builder`、`base image`、`registry mirror/proxy`、`proxy`、`cache`、`unknown`。
- `docs/acceptance/hil_runbook.md`
  - 新增 Docker-only host 边界：Docker 镜像 readiness 不等于 `hil_pass`。
  - 明确无 `/dev/ttyUSB*` 只能记录 blocked/preflight evidence。
  - 保留真实串口 handoff：`EXTRA_DOCKER_ARGS="--device=<real_serial_device>" bash scripts/docker_humble_dev.sh`。
- `docs/acceptance/robot_bringup_checklist.md`
  - 增加 Docker preflight 失败分类和 operator 下一步。
  - 明确 Docker success + no serial 仍然不是 HIL 通过。
- `OKR.md`
  - 更新 O1 当前证据：本轮把 Docker 阻断收敛到 registry mirror/proxy。

## 验证结果

### `bash -n scripts/docker_humble_build.sh scripts/docker_humble_dev.sh`

结果：通过，exit 0。

### `SKIP_COLCON=1 bash scripts/docker_humble_build.sh`

结果：失败，exit 1；失败允许，但已精确分类。

关键输出：

```text
base_image=osrf/ros:humble-desktop
ServerVersion=28.3.3 Driver=overlayfs DockerRootDir=/var/lib/docker RegistryMirrors=["https://ef4zg2yg.mirror.aliyuncs.com/","https://registry.dockermirror.com/","https://dockerpull.cn/","https://docker.m.daocloud.io/"]
#2 [internal] load metadata for docker.io/osrf/ros:humble-desktop
#2 ERROR: encountered unknown type text/html; children may not be fetched
ERROR: failed to build: failed to solve: osrf/ros:humble-desktop: failed to resolve source metadata for docker.io/osrf/ros:humble-desktop: encountered unknown type text/html; children may not be fetched
== Docker build failure classification ==
category=registry mirror/proxy
base_image=osrf/ros:humble-desktop
operator_next_step=A registry path returned HTML while fetching base image metadata/layers. Disable or change Docker registry mirror/proxy, clear the affected builder cache if needed, then rerun.
```

归因：`registry mirror/proxy`。Docker daemon 可用，当前 context 为 `desktop-linux`；可用 builder 正在运行。失败发生在 `docker.io/osrf/ros:humble-desktop` metadata 阶段，且 host Docker 配置了多个 registry mirror。

Operator 下一步：

1. 在 Docker Desktop/Engine 中临时关闭或更换 registry mirrors。
2. 单独运行 `docker pull osrf/ros:humble-desktop` 验证 base image metadata 是否恢复。
3. 如仍返回 HTML，换网络或清理当前 builder cache 后重跑 `SKIP_COLCON=1 bash scripts/docker_humble_build.sh`。

### `python3 scripts/hardware_smoke_wave_rover.py --status`

结果：通过，exit 0；输出为 software proof readiness。

关键输出：

```json
{
  "blocked_reason": "no_serial_candidates_found",
  "hil_ready": false,
  "pyserial_available": true,
  "serial_candidates": {
    "/dev/serial*": [],
    "/dev/ttyAMA*": [],
    "/dev/ttyUSB*": []
  },
  "source": "software_proof"
}
```

### `git diff --check -- <touched files>`

结果：通过，exit 0。

## 偏差

- 未修改 `docker/humble/Dockerfile`：阻断发生在 base image metadata 拉取/解析阶段，Dockerfile 内容尚未执行。
- 未修改 `scripts/docker_humble_dev.sh`：现有 `EXTRA_DOCKER_ARGS` 已覆盖真实串口设备透传需求。
- 未生成真实 HIL evidence packet：本机没有真实 WAVE ROVER/串口设备。

## 剩余风险

- Docker registry mirror/proxy 修复前，`ros-rbs-humble:dev` 仍无法在本机重建。
- 即使 Docker preflight 恢复，O1 仍缺真实 `hil_pass`：需要真实串口、WAVE ROVER、`T=1001` 反馈、`/odom`、`/imu/data`、`/battery` 样本和同一 `evidence_ref` 证据包。
