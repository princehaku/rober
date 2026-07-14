# O1 Same-Session PC Command Material Tech Plan

## 方案

在 `wave_rover_motion_map_hil_material_bundle.py` 中新增 same-session PC command material parser，读取：

- `sprints/2026.06.22_11-00_wheel_lr_samesession_first_jog/artifacts/02_pc_first_jog_samesession_timeoutfix.json`
- `sprints/2026.06.22_11-00_wheel_lr_samesession_first_jog/artifacts/03_base_status_after_pc_jog.json`

该 parser 只输出 safe summary，不回显 raw endpoint、URL、`/root/`、`/dev/tty*`、baudrate、raw T1001 frames、token 或 traceback。`remote_motion_key_values.wheel_feedback_lr_nonzero_proven=true` 只能以 `same_session_pc_command_` 前缀 material fact 表达，顶层安全字段继续固定 false。

## 接口影响

只扩展 O1 hardware bundle JSON additive fields。没有 ROS topic、service、launch 参数、WAVE ROVER command 或硬件配置行为变更。

## 文件范围

- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_motion_map_hil_material_bundle.py`
- `onboard/src/ros2_trashbot_hardware/test/test_wave_rover_motion_map_hil_material_bundle.py`
- `docs/hardware/wave_rover_motion_map_hil_material_bundle.md`
- `sprints/2026.07.11_02-34_o1_same_session_pc_command_material/tech-done.md`
- `sprints/2026.07.11_02-34_o1_same_session_pc_command_material/artifacts/hardware_worker_report.md`

## 验收命令

```bash
python3 -m py_compile onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/*.py
```

```bash
python3 -m unittest discover -s onboard/src/ros2_trashbot_hardware/test -p '*motion*map*hil*.py'
```

```bash
PYTHONPATH=onboard/src/ros2_trashbot_hardware python3 -m ros2_trashbot_hardware.wave_rover_motion_map_hil_material_bundle
```

```bash
rg -n "same_session_pc_command|same_session_hil_acceptance|blocked_missing_current_live_acceptance" onboard/src/ros2_trashbot_hardware docs/hardware sprints/2026.07.11_02-34_o1_same_session_pc_command_material
```

```bash
git diff --check -- onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_motion_map_hil_material_bundle.py onboard/src/ros2_trashbot_hardware/test/test_wave_rover_motion_map_hil_material_bundle.py docs/hardware/wave_rover_motion_map_hil_material_bundle.md sprints/2026.07.11_02-34_o1_same_session_pc_command_material
```

## 风险

- 该 material 是 historical same-session artifact，不是 current live rerun。
- PC proxy 里的 remote motion key values 可能与 after-jog base status latest zero feedback 并存，必须同时展示：motion-window material ready，after-jog readback still not HIL/safe-control proof。
- 若实现只包装已有 summary 而没有消费 `02` 和 `03` 两个具体 artifact，本轮不应上调 O1。

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 最低 Objective 是 O5，约 85%。
2. 本 sprint 不针对 O5，转向 O1。
3. 理由：O5 缺真实 external production evidence，最近 O5 support-only readiness packet 已固定 `okr_credit_allowed=false`，继续做 local/mock wrapper 会重复消费同一 external blocker。O1 虽约 92%，但存在未消费的同会话 PC command proxy 与 after-jog base status material，可在不宣称 HIL pass 的前提下推进 O1 evidence envelope。
4. final.md 收口时需复核：本轮是否真的消费了新的 `02`/`03` artifact delta；若只是 rollup 包装，则不得提升 OKR。
