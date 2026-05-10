# Sprint 2026.05.11 06-07 HIL + Route E2E Hardening-2 - Tech Plan

## 状态

- 阶段：tech-plan started（O1 聚焦）
- 时间：2026-05-11 06:00 Asia/Shanghai
- Owner：`hardware-engineer`
- 目标：先把 O1 实机围栏与证据链闭环，其他 KR 复位等待。

## 任务分工与文件范围

### `hardware-engineer`（主责：O1）

#### 文件范围

- `scripts/hardware_smoke_wave_rover.py`
- `docs/acceptance/wave_rover_hil_evidence.md`
- `docs/acceptance/robot_bringup_checklist.md`
- `docs/acceptance/hil_runbook.md`
- `docs/hardware/wave_rover_json_bridge.md`
- `sprints/2026.05.11_06-07_hil-route-e2e-hardening-2` 下本轮记录

#### 交付要求

1. 固定 `hil_pass` run 产物规范（`run_id`、`evidence_ref`、command/serial/feedback/三类 topic 快照）。
2. 复验 `T=143`、`T=142`、`T=131` 的 UART 命令链路，验证 `T=1001` 字段齐全。
3. 处理 `pyserial` 阻塞：`--help` 和 `--status` 可继续运行，`hil` 命令缺依赖时返回修复路径且不误报通过。
4. `source=software_proof` 与 `source=hil_pass` 在 evidence 文档内明确分离，不互相替代。

## 验收围栏（固定三条）

```bash
python3 scripts/hardware_smoke_wave_rover.py --help
python3 scripts/hardware_smoke_wave_rover.py --status
python3 scripts/hardware_smoke_wave_rover.py --move-test --test-speed 0.05 --test-duration-s 0.3 --serial-port /dev/ttyUSB0 --baudrate 115200
```

## 风险与阻塞

- pyserial 依赖缺失：记录为 `blocked`，不可把 `software_proof` 标记为 O1 通过。
- 串口路径不一致：按现场 `ls /dev/tty*` / `ls /dev/serial*` 重定向参数，不复制 Raspberry Pi 示例路径。
- `/odom`、`/imu/data`、`/battery` 映射说明与实机 run 证据未闭环前，不得清零残差风险。
