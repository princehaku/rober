# Sprint 2026.05.11_10-11 HIL Docker Preflight To Real Run - Final

## 状态

- 阶段：final blocked by hardware/docker
- 时间：2026-05-11 20:04 Asia/Shanghai
- 结论：本轮完成 O1 HIL preflight 可诊断性和 O2/O3 same-`evidence_ref` 软件支撑；真实 `hil_pass` 仍因本机无串口设备 blocked，Docker/Humble preflight 也被基础镜像 metadata 阻断。

## 本轮完成

- 创建 sprint 入口文档：`pre_start.md`、`prd.md`、`tech-plan.md`。
- 增强 WAVE ROVER smoke `--status`：串口候选扫描、pyserial 状态、`hil_ready`、`blocked_reason`、required evidence files、source boundary。
- 补齐 HIL runbook/evidence 文档中的 preflight 边界。
- 补齐 task record / diagnostics / operator gateway 的 `route_progress` 透传。
- 增强 `scripts/evidence_crosscheck.py` 对 `--task-record-dir` 和缺 route-level 字段的核验。
- 删除并排除偏航 sprint 目录 `2026.05.11_10-11_o2-task-recovery-route-replay-docker-proof`，避免主线从 O1 漂移。

## 验证摘要

- `python3 scripts/hardware_smoke_wave_rover.py --status`：通过，当前输出 `hil_ready=false`、`blocked_reason=no_serial_candidates_found`。
- `python3 -m py_compile` scoped：通过。
- behavior targeted unittest：`Ran 42 tests ... OK`。
- scoped `git diff --check`：通过。
- `SKIP_COLCON=1 bash scripts/docker_humble_build.sh`：失败，基础镜像 `osrf/ros:humble-desktop` metadata 解析为 `text/html`，Docker/Humble 容器内 preflight 未完成。

## OKR 影响

- O1：完成度保持约 75%。本轮提升了 preflight 可审计性，但没有真实 `hil_pass`。
- O2：完成度保持约 76%。本轮补强软件复盘字段，但缺真实任务 run。
- O3：完成度保持约 76%。本轮补强对账工具，但缺真实 route/Nav2 run。

## 下一步

1. 先修复 Docker 基础镜像 metadata 问题，恢复 `ros-rbs-humble:dev` 构建或可用镜像。
2. 在有真实 WAVE ROVER/Orange Pi 串口环境后执行 real run：

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

3. 通过后再用同一 `<new_hil_run_ref>` 复账 fixed-route status、route replay 与 task record。
