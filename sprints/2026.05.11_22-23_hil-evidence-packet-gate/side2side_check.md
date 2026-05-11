# Sprint 2026.05.11_22-23 HIL Evidence Packet Gate - Side2Side Check

## 状态

- 阶段：side2side_check
- 时间：2026-05-11 22:15 Asia/Shanghai
- 对照对象：`tech-plan.md` 中的 HIL evidence packet gate 验收口径。

## 对照结论

| Tech plan 要求 | 本轮结果 | 证据 |
| --- | --- | --- |
| 新增 Docker-only gate | 已完成 | `scripts/hil_evidence_packet_gate.py` |
| 不依赖 ROS2/serial | 已完成 | 脚本只使用标准库文件读取与 JSON 解析 |
| 必需文件检查 | 已完成 | `command.txt`、`serial.log`、`feedback_T1001.log`、`odom_once.jsonl`、`imu_once.jsonl`、`battery_once.jsonl` |
| 严格 `T=1001` 与 topic JSONL | 已完成 | blocked fixture 因缺 `T=1001`/topic sample 失败；synthetic fixture 通过 |
| blocked packet 不得误报 | 已完成 | `/tmp/rober_hil_gate_blocked` 输出 `status=blocked`，exit 1 |
| 合成完整 packet 可验证 gate | 已完成 | `/tmp/run_20260511T150000Z_ttyUSB0_hil_pass_speed0p050_dur0p30` 输出 `status=hil_pass`，exit 0 |
| 保留同一 `evidence_ref` | 已完成 | gate 输出 `evidence_ref` 并检测冲突 |
| 不修改 O2/O3 crosscheck | 已满足 | `python3 -m py_compile scripts/evidence_crosscheck.py` 通过，文件未改 |
| 不声明真实 HIL | 已满足 | docs/final 标注 synthetic fixture 不是真实硬件证据 |

## 用户验收视角

- 当前可验收为：packet gate 已可在 Docker-only 或普通 Python 环境中作为 O1 evidence 升级前置门。
- 当前不可验收为：真实 WAVE ROVER `hil_pass`。本机 `hardware_smoke_wave_rover.py --status` 仍显示 `blocked_reason=no_serial_candidates_found`。

## 证据边界

- `software_proof`：help、py_compile、`--status`、blocked fixture、synthetic fixture gate 逻辑。
- `blocked`：当前主机无串口候选，不能实车采集。
- `hil_pass`：仅真实 WAVE ROVER run 目录通过 gate 后才能用于 OKR/O1 进度；本轮没有产生真实 `hil_pass`。
