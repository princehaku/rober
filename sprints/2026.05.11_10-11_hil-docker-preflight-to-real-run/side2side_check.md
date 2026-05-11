# Sprint 2026.05.11_10-11 HIL Docker Preflight To Real Run - Side2Side Check

## 状态

- 阶段：side2side check
- 时间：2026-05-11 20:04 Asia/Shanghai

## 对照结果

| 目标 | 对照结果 | 证据 |
| --- | --- | --- |
| O1 优先，不能转去泛化 O2/O3 | 通过 | `OKR.md` 保持 O1 约 75%、O2/O3 约 76%；本轮 sprint 名称和收口仍是 HIL preflight to real run |
| Docker/software proof 不冒充 `hil_pass` | 通过 | `hardware_smoke_wave_rover.py --status` 输出 `source=software_proof`、`hil_ready=false`、`blocked_reason=no_serial_candidates_found` |
| 无硬件时继续功能前进 | 通过 | `--status` 现在能输出串口候选、依赖、required evidence files、source boundary；O2/O3 能严格对账 route_progress |
| 测试只做围栏 | 通过 | 仅运行硬件脚本 status/py_compile、behavior targeted unittest、scoped diff check |
| Docker preflight | 阻塞 | `SKIP_COLCON=1 bash scripts/docker_humble_build.sh` 在解析 `osrf/ros:humble-desktop` metadata 时失败：`unknown type text/html` |
| 真实 HIL 不虚报 | 通过 | 未运行 `--move-test`，未生成新的 `source=hil_pass` evidence packet |

## 不可放行项

- 当前无真实 WAVE ROVER UART 候选，O1 仍 blocked。
- 当前 Docker 基础镜像 metadata 解析失败，容器内 preflight 未完成。
- 本轮没有 `/odom`、`/imu/data`、`/battery` 实机样本。
- 本轮没有真实 fixed-route/Nav2 行驶样本。

## 下轮 Gate

1. 修复 Docker registry/cache 或基础镜像源，恢复 Humble 容器 preflight。
2. 在真实硬件主机确认串口路径。
3. 通过 Docker `--device=<real_serial_device>` 映射设备。
4. 运行低速 `--move-test` 并归档同一 `evidence_ref` 的 required evidence files。
5. 用 task_record/status/replay 对同一 `evidence_ref` 做复账。
