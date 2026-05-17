# WAVE ROVER Feedback Replay Gate

## Vendor sources

本 gate 的硬件事实只来自本地 vendor 资料：

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/hardware/wave_rover_json_bridge.md`

已采用的 vendor 结论：

- WAVE ROVER 上下位机链路是 UART newline-delimited JSON。
- `json_cmd.h` 定义 `FEEDBACK_BASE_INFO 1001`，本 gate 只接受 `T=1001`。
- `json_cmd.h` / 项目桥接文档约束 base feedback frame 至少包含 `L,R,r,p,y,v`。
- `base_ctrl.py` 使用 `json.loads(...readline...)` 读取一行 JSON，发送命令时追加 `\n`。
- `config.yaml` 有 `feedback_interval` 配置，但本 gate 不把合成 interval 当成实机频率。

## Scope

`pc-tools/evidence/wave_rover_feedback_replay_gate.py` 是 dependency-free PC gate：

- 只读取 `feedback_T1001.log`、`odom_once.jsonl`、`imu_once.jsonl`、`battery_once.jsonl`。
- 不打开 serial，不 import ROS2，不访问 WAVE ROVER，不发布 `/odom`、`/imu/data`、`/battery`。
- 支持直接 JSON `{"T":1001,...}`，也支持 wrapper JSON 的 `timestamp` / `t` / `time` / `monotonic_time` 与 `feedback` / `payload` / `message` 字段。
- 输出 `schema=trashbot.wave_rover_feedback_replay.v1`。
- 输出 `evidence_boundary=software_proof_docker_wave_rover_feedback_replay_gate`。
- 输出 `source=software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

本轮结果只能是 `software_proof_docker_wave_rover_feedback_replay_gate`，不是 `hil_pass`。

## Fail-closed rules

feedback replay：

- 缺 `feedback_T1001.log`、坏 JSON、非 object、非 `T=1001`、缺 `L,R,r,p,y,v` 均 blocked。
- timestamp-less `T=1001` 可以证明“可解析”，但 `interval_status=blocked_missing_timestamps`。
- 有至少 2 个 timestamp 时计算 interval count、min、max、median、large gap。
- timestamp 逆序或 large gap 均 blocked，不升级成 HIL pass。

topic alignment：

- `odom_once.jsonl`、`imu_once.jsonl`、`battery_once.jsonl` 每个文件至少一条 JSON object。
- `evidence_ref` 可在顶层、`header.evidence_ref`、`evidence.evidence_ref`、`route_progress.evidence_ref`。
- 三个 once 文件必须共享同一个 safe evidence_ref；`--evidence-ref` 存在时也必须一致。
- `odom` 至少有 pose/twist/position/orientation/linear/angular 之一。
- `imu` 至少有 orientation/angular_velocity/linear_acceleration/rpy/yaw 之一。
- `battery` 至少有 voltage/percentage/power_supply_status/current 之一。

## Example

```bash
python3 pc-tools/evidence/wave_rover_feedback_replay_gate.py \
  pc-tools/evidence/fixtures/wave_rover_feedback_replay/pass/feedback_T1001.log \
  pc-tools/evidence/fixtures/wave_rover_feedback_replay/pass/odom_once.jsonl \
  pc-tools/evidence/fixtures/wave_rover_feedback_replay/pass/imu_once.jsonl \
  pc-tools/evidence/fixtures/wave_rover_feedback_replay/pass/battery_once.jsonl \
  --evidence-ref run-wave-replay-pass \
  --summary-output /tmp/wave_rover_feedback_replay_summary.json \
  --once-json
```

## Next required evidence

真实上车前仍需补齐：

- 真实 WAVE ROVER HIL 采集的 `feedback_T1001.log`。
- 同一 run 的 `odom_once.jsonl`、`imu_once.jsonl`、`battery_once.jsonl`。
- 同一个 safe `evidence_ref` 绑定 command、serial、feedback、topic once snapshots。
- 现场报告单独声明 source 是否达到 `hil_pass`；本 gate 不会替现场声明。
