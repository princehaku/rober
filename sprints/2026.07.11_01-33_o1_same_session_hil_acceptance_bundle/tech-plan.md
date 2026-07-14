# O1 Same-Session HIL Acceptance Bundle Tech Plan

## 方案

在 `wave_rover_motion_map_hil_material_bundle.py` 中新增 same-session wheel feedback additive parser，读取 `2026.06.22_11-00_wheel_lr_samesession_first_jog/artifacts/01_upper_manual_samesession_012.json`。该 parser 只消费 allowlisted 字段：

- `schema=trashbot.upper_robot_api.v1.base_manual_result`
- `accepted=true`
- `manual_command_executed=true`
- `auto_stop_executed=true`
- `feedback_during_motion_attempted=true`
- `feedback_during_motion.t1001_feedback_status=observed`
- `feedback_during_motion.wheel_feedback_summary.lr_nonzero_observed=true`
- `feedback_during_motion.wheel_feedback_summary.latest_nonzero_pair.left_speed/right_speed`

输出 additive fields 建议：

- `same_session_wheel_feedback_material_present=true`
- `same_session_wheel_feedback_material_status=same_session_wheel_feedback_material_ready_not_hil_pass`
- `same_session_wheel_feedback_lr_nonzero_material_present=true`
- `same_session_wheel_feedback_latest_nonzero_pair={left_speed,right_speed,sign_pattern}`
- `same_session_wheel_feedback_motion_window_nonzero_pair_count=1`
- `same_session_hil_acceptance_status=blocked_missing_current_live_acceptance`
- `same_session_hil_acceptance_missing_fields=[external_video_recorded, physical_motion_lidar_delta_proven, current_live_hil_acceptance_record, current_live_nav2_route_execution_success]`
- `same_session_hil_acceptance_ready_not_hil_pass=true`

保持所有顶层 false safety fields，不复用裸名 `wheel_feedback_lr_nonzero_proven=true` 作为顶层字段，避免误导为 HIL pass。

## 接口影响

只扩展 O1 hardware bundle 输出 JSON additive fields。没有 ROS topic、service、launch 参数或 WAVE ROVER command 行为变更。

## 文件范围

- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_motion_map_hil_material_bundle.py`
- `onboard/src/ros2_trashbot_hardware/test/test_wave_rover_motion_map_hil_material_bundle.py`
- `docs/hardware/wave_rover_motion_map_hil_material_bundle.md`
- `sprints/2026.07.11_01-33_o1_same_session_hil_acceptance_bundle/tech-done.md`
- `sprints/2026.07.11_01-33_o1_same_session_hil_acceptance_bundle/artifacts/hardware_worker_report.md`

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
rg -n "same_session_wheel_feedback|same_session_hil_acceptance|blocked_missing_current_live_acceptance" onboard/src/ros2_trashbot_hardware docs/hardware sprints/2026.07.11_01-33_o1_same_session_hil_acceptance_bundle
```

```bash
git diff --check -- onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_motion_map_hil_material_bundle.py onboard/src/ros2_trashbot_hardware/test/test_wave_rover_motion_map_hil_material_bundle.py docs/hardware/wave_rover_motion_map_hil_material_bundle.md sprints/2026.07.11_01-33_o1_same_session_hil_acceptance_bundle
```

## 风险

- 该 material 是 historical same-session artifact，不是本轮 current live rerun。
- 原始 artifact 含 `/dev/ttyS5`、`115200`、endpoint 和 raw compact frames；最终 bundle 必须只输出安全投影。
- 若只做字段包装且没有新 current live artifact，本轮不应上调 O1。

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 最低 Objective 是 O5，约 85%。
2. 本 sprint 不针对 O5，转向 O1。
3. 理由：O5 本轮缺真实 external production evidence；最近 O5 support-only readiness packet 已固定 `okr_credit_allowed=false`，继续做 local/mock wrapper 会重复消费同一 external blocker。O1 虽约 92%，但仍有可推进的软件验收合同：把 same-session L/R 非零材料接入 composite HIL acceptance gap view，并明确不重复计分。
