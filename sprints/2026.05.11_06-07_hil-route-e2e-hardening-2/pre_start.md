# Sprint 2026.05.11 06-07 HIL + Route E2E Hardening-2 - Pre Start

## 状态

- 阶段：pre-start started（重聚焦 O1）
- 时间：2026-05-11 06:00 Asia/Shanghai
- 目录：`sprints/2026.05.11_06-07_hil-route-e2e-hardening-2/`
- Owner：`hardware-engineer`
- 本轮目标：优先完成 O1/HIL 首轮实机闭环；其余 O2/O3 仅在 `hil_pass` 阻塞解除后恢复。

## 启动依据（证据驱动）

1. `sprints/2026.05.10_21-22_review-progress-metrics/tech-done.md` 与 `final.md` 复盘到 `NO TESTS RAN`，围栏命名与执行链存在复发风险。
2. `docs/acceptance/hil_runbook.md` 与 `docs/acceptance/wave_rover_hil_evidence.md` 尚未形成第一轮 `source=hil_pass` 的统一证据包（尤其命令、反馈、topic快照与 `evidence_ref`）。
3. 历史 `scripts/hardware_smoke_wave_rover.py --status` 可跑，但 pyserial 缺失会直接阻断 hil_pass；该阻塞已在最近评审被反复提及，当前仍影响闭环。
4. `docs/hardware/wave_rover_json_bridge.md` 的映射表已齐备，但与第一轮 run 的 `T=143/T=142/T=131/T=1001` 复验尚未按证据链固定。

## 本轮核心抓手（O1）

### 1) 先把 `hil_pass` 做成可重现实机证据闭环

- 动作：固定第一轮 run 的 `run_id` + `evidence_ref`，并要求 evidence 文档保留 command、serial log、两帧以上 `T=1001`、主题快照。
- 证据链：`docs/acceptance/hil_runbook.md`、`docs/acceptance/wave_rover_hil_evidence.md`、`docs/acceptance/robot_bringup_checklist.md`。
- 验收：至少一次完整 `source=hil_pass` run 后，能从 `wave_rover_hil_evidence.md` 回查同一 evidence。

### 2) `cmd_vel` 与底盘映射复验（命令-反馈一体）

- 动作：围栏命令固定验证启动下发顺序（`T=143`、`T=142`、`T=131`）、`T=1001` 字段完整性、`L/R/r/p/y/v` + 回环反馈频率。
- 证据链：`scripts/hardware_smoke_wave_rover.py`、`docs/hardware/wave_rover_json_bridge.md`、`docs/acceptance/hil_runbook.md`。
- 验收：`hil_pass` 日志中出现上述序列与字段，`/odom` `/imu/data` `/battery` 源头说明齐全。

### 3) 依赖阻塞（pyserial / 串口）作为硬边界，不替代通过

- 动作：在脚本中明确 pyserial 缺失时不误报；`--help` 与 `--status` 仍可执行，硬件围栏禁止在依赖阻塞下伪通过。
- 证据链：`scripts/hardware_smoke_wave_rover.py`、`AGENTS.md`、`docs/acceptance/robot_bringup_checklist.md`。
- 验收：未安装依赖时显示明确修复路径；依赖修复后执行 `--move-test`。

## 围栏策略（本轮不加新测试矩阵）

- 围栏固定三条：
  - `python3 scripts/hardware_smoke_wave_rover.py --help`
  - `python3 scripts/hardware_smoke_wave_rover.py --status`
  - `python3 scripts/hardware_smoke_wave_rover.py --move-test --test-speed 0.05 --test-duration-s 0.3 --serial-port /dev/ttyUSB0 --baudrate 115200`
- 禁止 `test_*review*py` 通配验收；任何失败必须以 residual risk 形式进入 `tech-done`。
