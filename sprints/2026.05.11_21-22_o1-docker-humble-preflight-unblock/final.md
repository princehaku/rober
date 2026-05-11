# Sprint 2026.05.11_21-22 O1 Docker Humble Preflight Unblock - Final

## 状态

- 阶段：final blocked by Docker registry mirror/proxy and missing hardware
- 时间：2026-05-11 21:14 Asia/Shanghai
- 结论：本轮完成 O1 Docker/Humble preflight 诊断增强和 HIL 边界同步；Docker 构建仍 blocked，但已归因为 registry mirror/proxy 返回 HTML；没有真实硬件，不产生 `hil_pass`。

## 本轮完成

- 增强 `scripts/docker_humble_build.sh`：
  - 输出 Docker daemon、context、builder、base image、storage driver、registry mirrors、proxy env set/unset。
  - 捕获 build 日志并在失败时分类输出。
  - 当前失败分类为 `registry mirror/proxy`。
- 更新 HIL runbook/checklist：
  - Docker-only host 和无 `/dev/ttyUSB*` 只能记录 readiness/blocked evidence。
  - `python3 scripts/hardware_smoke_wave_rover.py --status` 是 `source=software_proof`。
  - 真实上车仍需通过 `EXTRA_DOCKER_ARGS="--device=<real_serial_device>" bash scripts/docker_humble_dev.sh` 传入串口。
- 更新 OKR O1 证据，不虚增完成度。

## 验证摘要

- `bash -n scripts/docker_humble_build.sh scripts/docker_humble_dev.sh`：通过。
- `SKIP_COLCON=1 bash scripts/docker_humble_build.sh`：失败，分类为 `registry mirror/proxy`。
- `python3 scripts/hardware_smoke_wave_rover.py --status`：通过，`hil_ready=false`、`blocked_reason=no_serial_candidates_found`、`source=software_proof`。
- `git diff --check -- <touched files>`：通过。

## OKR 影响

- O1：完成度保持约 75%。本轮没有真实 `hil_pass`，但把 Docker preflight 阻断变成可操作诊断。
- O2/O3：不变。本轮未触碰行为、导航或 same-`evidence_ref` contract。

## 下一步

1. Operator 在 Docker Desktop/Engine 中关闭或更换 registry mirrors/proxy，然后运行：

```bash
docker pull osrf/ros:humble-desktop
SKIP_COLCON=1 bash scripts/docker_humble_build.sh
```

2. Docker preflight 恢复后，在有真实 WAVE ROVER/串口的机器上运行：

```bash
EXTRA_DOCKER_ARGS="--device=<real_serial_device>" bash scripts/docker_humble_dev.sh
python3 scripts/hardware_smoke_wave_rover.py \
  --move-test \
  --test-speed 0.05 \
  --test-duration-s 0.3 \
  --serial-port <real_serial_device> \
  --baudrate 115200 \
  --evidence-ref <new_hil_run_ref>
```

3. 只有采到真实 `T=1001`、`/odom`、`/imu/data`、`/battery` 并归档同一 `evidence_ref` 后，才能登记 O1 `hil_pass`。
