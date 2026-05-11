# Sprint 2026.05.11_22-23 HIL Evidence Packet Gate - Tech Done

## 状态

- 阶段：tech-done
- 时间：2026-05-11 22:15 Asia/Shanghai
- Owner：`hardware-engineer`
- 结论：Docker-only 文件层 HIL evidence packet gate 已就绪；本机没有真实 WAVE ROVER/串口，真实 `hil_pass` 仍 pending，O1 完成度不升级。

## 已读资料

- `AGENTS.md`
- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `sprints/2026.05.11_22-23_hil-evidence-packet-gate/tech-plan.md`
- `sprints/2026.05.11_21-22_o1-docker-humble-preflight-unblock/tech-done.md`

## 采用的 vendor 事实

- WAVE ROVER 上下位机链路是 UART，UTF-8 JSON，按 `\n` 分帧。
- Vendor Raspberry Pi 参考使用 `/dev/ttyAMA0`、`115200`；Orange Pi 实车串口仍需现场确认，不能硬编码。
- `CMD_BASE_FEEDBACK_FLOW` 为 `T=131`，`CMD_FEEDBACK_FLOW_INTERVAL` 为 `T=142`，`CMD_UART_ECHO_MODE` 为 `T=143`。
- `FEEDBACK_BASE_INFO` 为 `T=1001`；真实 HIL packet 至少要有可解析 `T=1001` 反馈样本。

## 实际改动

- `scripts/hil_evidence_packet_gate.py`
  - 新增纯 Python 文件层 gate，不依赖 ROS2、pyserial 或串口设备。
  - 输入：`--packet-dir <evidence_run_dir>`。
  - 输出 JSON：`status`、`evidence_ref`、`source`、`blocked_reason`、`failures`、`checks`、`vendor_sources`。
  - 严格 `hil_pass`：六个必需文件存在且非空；`feedback_T1001.log` 至少一条可解析 `T=1001` JSON；`odom_once.jsonl`、`imu_once.jsonl`、`battery_once.jsonl` 各至少一条可解析 JSON object；`serial.log` 不能只是串口失败/blocked；`command.txt` 必须能追踪 smoke 或 move-test；`source` 与 `evidence_ref` 不能互相矛盾。
  - `blocked`：缺文件、空文件、串口打开失败、无 `T=1001`、topic sample 缺失或不可解析、非 HIL source、`evidence_ref` 冲突均返回非 0。
  - `software_proof`：只在 `--allow-software-proof` 且 status-only/template packet 场景允许输出，仍非 0，不能冒充 `hil_pass`。
- `docs/acceptance/wave_rover_hil_evidence.md`
  - 增加 gate 使用方式和 `hil_pass` 证据边界。
- `docs/acceptance/hil_runbook.md`
  - 增加 evidence packet gate 步骤、检查项和 vendor 来源。
- `docs/acceptance/robot_bringup_checklist.md`
  - 增加 post-run gate 要求和 Docker-only/synthetic fixture 边界。

## 验证结果

### `python3 scripts/hil_evidence_packet_gate.py --help`

结果：通过，exit 0。关键输出：

```text
usage: hil_evidence_packet_gate.py [-h] --packet-dir PACKET_DIR
                                   [--allow-software-proof]
```

### `python3 -m py_compile scripts/hil_evidence_packet_gate.py`

结果：通过，exit 0。

### `python3 scripts/hardware_smoke_wave_rover.py --status`

结果：通过，exit 0；输出仍是 software proof readiness，不是 HIL。

```json
{
  "blocked_reason": "no_serial_candidates_found",
  "hil_ready": false,
  "pyserial_available": true,
  "source": "software_proof"
}
```

### Blocked fixture gate

命令：`python3 scripts/hil_evidence_packet_gate.py --packet-dir /tmp/rober_hil_gate_blocked`

结果：按预期 blocked，exit 1。

```json
{
  "status": "blocked",
  "blocked_reason": "empty_required_file:odom_once.jsonl",
  "failures": [
    "empty_required_file:odom_once.jsonl",
    "serial_log_blocked:serial failure",
    "missing_parseable_T1001_feedback",
    "missing_parseable_topic_sample:odom_once.jsonl"
  ]
}
```

### Synthetic valid fixture gate

命令：`python3 scripts/hil_evidence_packet_gate.py --packet-dir /tmp/run_20260511T150000Z_ttyUSB0_hil_pass_speed0p050_dur0p30`

结果：synthetic fixture 通过 gate，exit 0。

```json
{
  "status": "hil_pass",
  "evidence_ref": "run_20260511T150000Z_ttyUSB0_hil_pass_speed0p050_dur0p30",
  "failures": []
}
```

说明：这是 `/tmp` 合成 fixture，只证明 gate 逻辑能识别完整 packet；当前本机没有真实 WAVE ROVER/串口，不能登记为真实硬件 `hil_pass`。

### `python3 -m py_compile scripts/evidence_crosscheck.py`

结果：通过，exit 0；本轮未修改 O2/O3 crosscheck。

## 偏差

- 未修改 `scripts/hardware_smoke_wave_rover.py`：本轮选择独立 gate，避免让硬件 smoke 承担离线归档校验职责。
- 未触碰 task orchestrator、nav、operator UI 或 `scripts/evidence_crosscheck.py`。
- 未生成真实 evidence 目录；只在 `/tmp` 创建 blocked 和 synthetic fixture 做围栏验证。

## 剩余风险

- 真实 O1 `hil_pass` 仍等待 WAVE ROVER、现场确认串口、串口透传到 Docker、真实 `T=1001`、ROS topic samples 和同一 `evidence_ref` 归档。
- Synthetic fixture 通过不能证明硬件接线、方向、里程、IMU 或电池语义。
- 下一步实车 run 后必须用同一 `evidence_ref` 交给 `scripts/evidence_crosscheck.py` 复账 O2/O3。
